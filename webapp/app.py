import subprocess
import json
import os
import re
from flask import Flask, render_template, abort

app = Flask(__name__)

# --- Data Loading and Processing ---
TOOL_DATA_CATEGORIES = {} # Dict to store categories by slug: {category_slug: category_data}
TOOL_DATA_TOOLS = {}      # Dict to store tools by category_slug and tool_slug: {(category_slug, tool_slug): tool_data}

def slugify(text):
    """Generates a URL-friendly slug from text."""
    if text is None:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)  # Remove non-alphanumeric characters except spaces and hyphens
    text = re.sub(r'\s+', '-', text)          # Replace spaces with hyphens
    text = re.sub(r'-+', '-', text)           # Replace multiple hyphens with a single one
    return text.strip('-')

def load_tool_data():
    """Loads and processes tool data from discover_tools.py."""
    global TOOL_DATA_CATEGORIES, TOOL_DATA_TOOLS
    processed_categories = {}
    processed_tools = {}

    # Path to discover_tools.py, assuming app.py is in webapp/ and discover_tools.py is in the parent directory
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'discover_tools.py')
    
    try:
        result = subprocess.run(['python3', script_path], capture_output=True, text=True, check=True, cwd=os.path.join(os.path.dirname(script_path)))
        raw_data = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running discover_tools.py: {e}")
        print(f"Stderr: {e.stderr}")
        raw_data = [] # Use empty data to prevent crash, or handle more gracefully
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from discover_tools.py: {e}")
        raw_data = []
    except FileNotFoundError:
        print(f"Error: discover_tools.py not found at {script_path}")
        raw_data = []

    for category_idx, category in enumerate(raw_data):
        category_title = category.get("category_title", f"Unnamed Category {category_idx}")
        category_slug = slugify(category_title)
        if not category_slug:
            category_slug = f"category-{category_idx}" # Fallback slug

        if category_slug in processed_categories: # Ensure unique category slugs
            print(f"Warning: Duplicate category slug '{category_slug}' generated for title '{category_title}'. Appending index.")
            temp_slug = category_slug
            i = 1
            while temp_slug in processed_categories:
                temp_slug = f"{category_slug}-{i}"
                i += 1
            category_slug = temp_slug
            
        category_info = {
            "title": category_title,
            "slug": category_slug,
            "tools": [] # Will store lightweight tool info: {"title", "slug", "description"}
        }
        
        for tool_idx, tool in enumerate(category.get("tools", [])):
            tool_title = tool.get("title", f"Unnamed Tool {tool_idx}")
            tool_slug = slugify(tool_title)
            if not tool_slug:
                tool_slug = f"tool-{tool_idx}" # Fallback slug

            # Ensure tool slug is unique within this category
            current_tool_slugs_in_category = {t['slug'] for t in category_info["tools"]}
            if tool_slug in current_tool_slugs_in_category:
                print(f"Warning: Duplicate tool slug '{tool_slug}' for title '{tool_title}' in category '{category_title}'. Appending index.")
                temp_tool_slug = tool_slug
                j = 1
                while temp_tool_slug in current_tool_slugs_in_category:
                    temp_tool_slug = f"{tool_slug}-{j}"
                    j += 1
                tool_slug = temp_tool_slug

            tool_details = {
                "title": tool_title,
                "slug": tool_slug,
                "description": tool.get("description", "No description available."),
                "install_commands": tool.get("install_commands", []),
                "run_commands": tool.get("run_commands", []),
                "execution_type": tool.get("execution_type", "not_runnable"),
                "project_url": tool.get("project_url"),
                "custom_input_fields": [] # Default to empty
            }

            # Add specific metadata for Host2IP and Striker
            if tool_title == "Host to IP " and tool_details["execution_type"] == "custom_run":
                tool_details["custom_input_fields"] = [{"name": "host_name", "label": "Enter host name:"}]
                tool_details["custom_tool_id"] = "host2ip"
            elif tool_title == "Striker" and tool_details["execution_type"] == "custom_run":
                tool_details["custom_input_fields"] = [{"name": "site_name", "label": "Enter site to scan (e.g., example.com):"}]
                tool_details["custom_tool_id"] = "striker"
            
            category_info["tools"].append({
                "title": tool_title,
                "slug": tool_slug,
                "description": tool_details["description"][:100] + "..." if tool_details["description"] and len(tool_details["description"]) > 100 else tool_details["description"] # Short description for category page
            })
            processed_tools[(category_slug, tool_slug)] = tool_details
        
        processed_categories[category_slug] = category_info
    
    TOOL_DATA_CATEGORIES = processed_categories
    TOOL_DATA_TOOLS = processed_tools
    # print(f"Loaded {len(TOOL_DATA_CATEGORIES)} categories and {len(TOOL_DATA_TOOLS)} tools.")

# Need io for StringIO
import io
import sys # For sys.stdin, sys.stdout redirection

# Dynamically import tool classes - adjust path as necessary
# Assuming 'tools' is a package in the project root.
# The project root needs to be in sys.path for these imports to work if app.py is in webapp/
project_root_for_imports = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root_for_imports not in sys.path:
    sys.path.insert(0, project_root_for_imports)

try:
    from tools.information_gathering_tools import Host2IP, Striker
except ImportError as e:
    print(f"Could not import tool classes: {e}. Custom tool execution will fail.")
    Host2IP = None  # Placeholder if import fails
    Striker = None  # Placeholder if import fails


# --- Routes ---
@app.route('/')
def index():
    """Displays the list of tool categories."""
    # Sort categories by title for consistent display
    sorted_categories = sorted(TOOL_DATA_CATEGORIES.values(), key=lambda c: c['title'])
    return render_template('index.html', categories=sorted_categories)

@app.route('/category/<category_slug>')
def category_view(category_slug):
    """Displays tools in a specific category."""
    category_data = TOOL_DATA_CATEGORIES.get(category_slug)
    if not category_data:
        abort(404)
    # Tools within category_data are already sorted if necessary or can be sorted here
    # category_data['tools'] is a list of dicts: {"title", "slug", "description"}
    return render_template('category.html', category=category_data)

@app.route('/tool/<category_slug>/<tool_slug>')
def tool_view(category_slug, tool_slug):
    """Displays details for a specific tool."""
    tool_data = TOOL_DATA_TOOLS.get((category_slug, tool_slug))
    category_data = TOOL_DATA_CATEGORIES.get(category_slug) # For breadcrumbs or category context
    if not tool_data or not category_data:
        abort(404)
    return render_template('tool.html', tool=tool_data, category=category_data)


@app.route('/run_custom_tool/<category_slug>/<tool_slug>', methods=['GET', 'POST'])
def run_custom_tool_view(category_slug, tool_slug):
    tool_data = TOOL_DATA_TOOLS.get((category_slug, tool_slug))
    category_data = TOOL_DATA_CATEGORIES.get(category_slug)

    if not tool_data or not category_data:
        abort(404)

    if not tool_data.get("custom_tool_id"):
        print(f"Tool {tool_data.get('title')} is not configured for custom execution via web UI.")
        abort(404) # Not a supported custom tool

    output_lines = []
    project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    execution_succeeded = False # Default to False for custom tools until success is confirmed

    if request.method == 'POST':
        custom_tool_id = tool_data.get("custom_tool_id")
        
        if custom_tool_id == "host2ip":
            if not Host2IP:
                output_lines.append("Error: Host2IP tool class not loaded.\n")
                execution_succeeded = False
            else:
                host_name = request.form.get("host_name")
                if not host_name:
                    output_lines.append("Error: Host name is required for Host2IP.\n")
                    execution_succeeded = False
                else:
                    output_lines.append(f"$ Running Host2IP with input: {host_name}\n")
                    tool_instance = Host2IP()
                    
                    # Redirect stdin, stdout, stderr
                    original_stdin = sys.stdin
                    original_stdout = sys.stdout
                    original_stderr = sys.stderr
                    sys.stdin = io.StringIO(host_name + '\n')
                    captured_stdout = io.StringIO()
                    captured_stderr = io.StringIO()
                    sys.stdout = captured_stdout
                    sys.stderr = captured_stderr
                    
                    host_ip_execution_exception = None
                    try:
                        tool_instance.run() # This will use the redirected stdio
                    except Exception as e:
                        output_lines.append(f"Error during Host2IP execution: {str(e)}\n")
                        host_ip_execution_exception = e
                    finally:
                        sys.stdin = original_stdin
                        sys.stdout = original_stdout
                        sys.stderr = original_stderr
                    
                    std_output_val = captured_stdout.getvalue()
                    std_error_val = captured_stderr.getvalue()

                    output_lines.append(std_output_val)
                    if std_error_val:
                        output_lines.append(f"STDERR:\n{std_error_val}")
                    
                    # Host2IP success criteria: no exception AND no stderr output.
                    # clear_screen() might write to stderr, so we need to be careful or ignore specific stderr.
                    # For simplicity, we'll consider any stderr as a potential issue for now.
                    if host_ip_execution_exception is None and not std_error_val: # (std_error_val might contain clear_screen() codes)
                        execution_succeeded = True 
                        # A more robust check might be to see if std_output_val contains an IP.
                        # For now, if it runs and stderr is empty (ignoring clear screen effects), consider it okay.
                        if not std_output_val.strip(): # If stdout is empty, it likely failed to find IP
                            output_lines.append("Host2IP ran, but no IP was returned (stdout is empty).\n")
                            execution_succeeded = False

                    output_lines.append("-" * 30 + "\n")

        elif custom_tool_id == "striker":
            if not Striker: 
                 output_lines.append("Error: Striker tool class not loaded.\n")
                 execution_succeeded = False
            else:
                site_name = request.form.get("site_name")
                if not site_name:
                    output_lines.append("Error: Site name is required for Striker.\n")
                    execution_succeeded = False
                else:
                    output_lines.append(f"$ Running Striker for site: {site_name}\n")
                    striker_dir = os.path.join(project_root_dir, "Striker") 
                    striker_script_path = os.path.join(striker_dir, "striker.py")

                    if not os.path.isdir(striker_dir) or not os.path.isfile(striker_script_path):
                        output_lines.append(f"Error: Striker directory or script not found at {striker_dir}.\n")
                        output_lines.append("Please ensure Striker is cloned as 'Striker' in the project root.\n")
                        execution_succeeded = False
                    else:
                        command_to_run = ["sudo", "python3", "striker.py", site_name]
                        try:
                            process = subprocess.Popen(
                                command_to_run,
                                cwd=striker_dir, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True
                            )
                            stdout, stderr = process.communicate()
                            if stdout:
                                output_lines.append(stdout)
                            if stderr:
                                output_lines.append(f"STDERR: {stderr}")
                            
                            if process.returncode == 0:
                                execution_succeeded = True
                            else:
                                output_lines.append(f"Striker exited with error code: {process.returncode}\n")
                                execution_succeeded = False
                        except Exception as e:
                            output_lines.append(f"Failed to execute Striker: {str(e)}\n")
                            execution_succeeded = False
                    output_lines.append("-" * 30 + "\n")
        else:
            output_lines.append(f"Error: Unknown custom tool ID '{custom_tool_id}'.\n")
            execution_succeeded = False

        return render_template('run_output.html', tool=tool_data, category=category_data, output="".join(output_lines), execution_succeeded=execution_succeeded)

    # For GET request, just show the page with the form (tool.html handles this)
    return render_template('tool.html', tool=tool_data, category=category_data)


@app.route('/run_tool/<category_slug>/<tool_slug>')
def run_tool_view(category_slug, tool_slug):
    """Executes a tool's run_commands and displays the output."""
    tool_data = TOOL_DATA_TOOLS.get((category_slug, tool_slug))
    category_data = TOOL_DATA_CATEGORIES.get(category_slug)

    if not tool_data or not category_data:
        abort(404)

    if tool_data.get("execution_type") != "run_commands" or not tool_data.get("run_commands"):
        # Or render an error message on tool_output.html like "Tool is not runnable or has no run commands."
        abort(404) # For now, keep it simple

    output_lines = []
    project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    overall_success = True # Assume success until a command fails

    for command in tool_data["run_commands"]:
        output_lines.append(f"$ {command}\n")
        try:
            # Using Popen for more control, but wait for each command to complete.
            # shell=True is used due to commands like 'cd dir && ./script'
            # The CWD is set to the project root where hackingtool.py resides.
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=project_root_dir 
            )
            stdout, stderr = process.communicate() # Waits for command to complete
            
            if stdout:
                output_lines.append(stdout)
            if stderr:
                output_lines.append(f"STDERR: {stderr}")
            
            if process.returncode != 0:
                output_lines.append(f"Command exited with error code: {process.returncode}\n")
                overall_success = False # Mark failure
            else:
                output_lines.append(f"Command completed successfully.\n")
            output_lines.append("-" * 30 + "\n")

        except Exception as e:
            output_lines.append(f"Failed to execute command '{command}': {str(e)}\n")
            overall_success = False # Mark failure
            output_lines.append("-" * 30 + "\n")
            # Continue to next command if one fails

    return render_template('run_output.html', tool=tool_data, category=category_data, output="".join(output_lines), execution_succeeded=overall_success)


@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 error page."""
    return render_template('404.html'), 404

# --- Load data at app start ---
load_tool_data()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
