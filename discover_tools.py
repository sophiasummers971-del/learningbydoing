import sys
import os
import json

# Add project root to sys.path to allow imports from core and tools
# Assuming this script is in the project root.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# It seems core.py is in the root, so HackingTool should be importable.
# hackingtool.py is also in the root.
from core import HackingTool, HackingToolsCollection
# We will import all_tools within main after importing hackingtool module

def get_tool_info(tool_instance): # Changed tool_class to tool_instance
    """Extracts information from a single tool instance."""
    tool_info_dict = {
        "title": "Unknown Tool",
        "description": "No description available.",
        "install_commands": [],
        "run_commands": [],
        "execution_type": "not_runnable",
        "project_url": None
    }

    try:
        # Access attributes directly from the instance
        tool_info_dict["title"] = getattr(tool_instance, 'TITLE', tool_info_dict["title"])
        tool_info_dict["description"] = getattr(tool_instance, 'DESCRIPTION', tool_info_dict["description"])
        
        install_cmds = getattr(tool_instance, 'INSTALL_COMMANDS', [])
        tool_info_dict["install_commands"] = list(install_cmds) if isinstance(install_cmds, (list, tuple)) else []
        
        run_cmds = getattr(tool_instance, 'RUN_COMMANDS', [])
        tool_info_dict["run_commands"] = list(run_cmds) if isinstance(run_cmds, (list, tuple)) else []
        
        tool_info_dict["project_url"] = getattr(tool_instance, 'PROJECT_URL', None)

        # Determine execution_type based on instance attributes and methods
        if tool_info_dict["run_commands"]:
            tool_info_dict["execution_type"] = "run_commands"
        else:
            # Check for 'run' method override and 'runnable' flag on the instance
            if getattr(tool_instance, 'runnable', False) and hasattr(tool_instance, 'run') and \
               tool_instance.run.__func__ is not HackingTool.run.__func__: # Check against HackingTool's run method
                tool_info_dict["execution_type"] = "custom_run"
            else:
                tool_info_dict["execution_type"] = "not_runnable" # Or "none" as per requirements

    except Exception as e:
        # We can log this error if needed: print(f"Could not process {tool_instance}: {e}", file=sys.stderr)
        pass # Keep default values for this tool

    return tool_info_dict

def main():
    # Import hackingtool here to get its 'all_tools'
    import hackingtool
    
    output_data = []
    if not hasattr(hackingtool, 'all_tools'):
        print(json.dumps({"error": "'all_tools' not found in hackingtool.py. Please ensure it is defined."}, indent=4), file=sys.stderr)
        return
        
    for collection_instance in hackingtool.all_tools:
        if not isinstance(collection_instance, HackingToolsCollection):
            print(f"Warning: Item in all_tools is not a HackingToolsCollection: {collection_instance}", file=sys.stderr)
            continue

        category_title = getattr(collection_instance, 'TITLE', 'Uncategorized')
        category_tools_data = []
        
        tools_list = getattr(collection_instance, 'TOOLS', [])
        if not isinstance(tools_list, list):
            print(f"Warning: TOOLS attribute in {category_title} is not a list.", file=sys.stderr)
            continue
            
        for tool_instance in tools_list: # Changed tool_class to tool_instance
            if tool_instance is None: # Skip if None is in the list
                continue
            
            # Check if it's an instance of HackingTool
            if not isinstance(tool_instance, HackingTool):
                 title = getattr(tool_instance, 'TITLE', 'Invalid Tool Entry') # Try to get a title
                 description = f"Entry '{title}' is not a valid HackingTool instance."
                 if not hasattr(tool_instance, 'TITLE'): # If it doesn't even have a TITLE
                     description = "Entry is not a valid HackingTool instance and has no TITLE."

                 category_tools_data.append({
                     "title": title,
                     "description": description,
                     "install_commands": [], "run_commands": [], "execution_type": "not_runnable", "project_url": None
                 })
                 continue

            tool_info = get_tool_info(tool_instance) # Pass instance
            category_tools_data.append(tool_info)
        
        output_data.append({
            "category_title": category_title,
            "tools": category_tools_data
        })
    
    print(json.dumps(output_data, indent=4))

if __name__ == "__main__":
    # Make sure to import hackingtool as a module object to access all_tools, done at the start of main()
    main()
