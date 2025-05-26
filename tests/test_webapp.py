import unittest
from unittest.mock import patch, MagicMock, call
import json
import io
import os
import sys

# Add project root to sys.path to allow importing webapp.app
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from webapp import app as flask_app # Flask app instance from webapp.app

# Mock data definition
MOCK_TOOL_JSON_OUTPUT = [
    {
        "category_title": "Test Category 1",
        "tools": [
            {
                "title": "RunCommands Tool",
                "description": "A tool that runs via commands.",
                "install_commands": ["apt-get install runtool"],
                "run_commands": ["runtool --execute"],
                "execution_type": "run_commands",
                "project_url": "http://example.com/runtool"
            },
            {
                "title": "Host to IP ", # Note the trailing space, matching actual tool
                "description": "Resolves host to IP.",
                "install_commands": [],
                "run_commands": [],
                "execution_type": "custom_run", # Will be identified by custom_tool_id: host2ip
                "project_url": ""
            },
            {
                "title": "Striker",
                "description": "Scans sites.",
                "install_commands": ["git clone striker"],
                "run_commands": [], # Striker's run is custom, not via run_commands
                "execution_type": "custom_run", # Will be identified by custom_tool_id: striker
                "project_url": "http://example.com/striker"
            },
            {
                "title": "Not Runnable Tool",
                "description": "A tool that is not runnable.",
                "install_commands": [],
                "run_commands": [],
                "execution_type": "not_runnable",
                "project_url": ""
            }
        ]
    },
    {
        "category_title": "Empty Category",
        "tools": []
    }
]

# Expected slugs (calculate them once for consistency in tests)
MOCK_CAT_SLUG = flask_app.slugify("Test Category 1")
MOCK_RUN_TOOL_SLUG = flask_app.slugify("RunCommands Tool")
MOCK_HOST2IP_SLUG = flask_app.slugify("Host to IP ")
MOCK_STRIKER_SLUG = flask_app.slugify("Striker")
MOCK_NOT_RUNNABLE_SLUG = flask_app.slugify("Not Runnable Tool")


class TestWebApp(unittest.TestCase):

    def setUp(self):
        """Set up test client and mock data loading for each test."""
        flask_app.app.config['TESTING'] = True
        flask_app.app.config['WTF_CSRF_ENABLED'] = False # Assuming no CSRF for simplicity
        self.client = flask_app.app.test_client()

        # Mock subprocess.run used by load_tool_data to return our mock JSON
        self.mock_subprocess_run = patch('webapp.app.subprocess.run').start()
        mock_process_result = MagicMock()
        mock_process_result.stdout = json.dumps(MOCK_TOOL_JSON_OUTPUT)
        mock_process_result.stderr = ""
        mock_process_result.returncode = 0
        self.mock_subprocess_run.return_value = mock_process_result
        
        # Call load_tool_data to populate TOOL_DATA_CATEGORIES and TOOL_DATA_TOOLS
        # This ensures that app globals are set using our mock data before each test
        flask_app.load_tool_data()

        # Stop the patcher after setUp if it's started here, or manage via self.addCleanup
        self.addCleanup(patch.stopall)


    def test_slugify_function(self):
        self.assertEqual(flask_app.slugify("Test Title!@#123"), "test-title-123")
        self.assertEqual(flask_app.slugify("Another   Example-Title"), "another-example-title")
        self.assertEqual(flask_app.slugify(None), "")
        self.assertEqual(flask_app.slugify(""), "")


    def test_load_tool_data_populates_globals(self):
        # This test effectively checks the state after setUp
        self.assertTrue(MOCK_CAT_SLUG in flask_app.TOOL_DATA_CATEGORIES)
        self.assertEqual(flask_app.TOOL_DATA_CATEGORIES[MOCK_CAT_SLUG]['title'], "Test Category 1")
        
        expected_run_tool_key = (MOCK_CAT_SLUG, MOCK_RUN_TOOL_SLUG)
        self.assertTrue(expected_run_tool_key in flask_app.TOOL_DATA_TOOLS)
        self.assertEqual(flask_app.TOOL_DATA_TOOLS[expected_run_tool_key]['title'], "RunCommands Tool")
        self.assertEqual(flask_app.TOOL_DATA_TOOLS[expected_run_tool_key]['execution_type'], "run_commands")

        # Check Host2IP metadata (set in load_tool_data)
        expected_host2ip_key = (MOCK_CAT_SLUG, MOCK_HOST2IP_SLUG)
        self.assertTrue(expected_host2ip_key in flask_app.TOOL_DATA_TOOLS)
        self.assertEqual(flask_app.TOOL_DATA_TOOLS[expected_host2ip_key]['custom_tool_id'], "host2ip")
        
        # Check Striker metadata
        expected_striker_key = (MOCK_CAT_SLUG, MOCK_STRIKER_SLUG)
        self.assertTrue(expected_striker_key in flask_app.TOOL_DATA_TOOLS)
        self.assertEqual(flask_app.TOOL_DATA_TOOLS[expected_striker_key]['custom_tool_id'], "striker")


    # --- Basic Route Tests ---
    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test Category 1", response.data)

    def test_category_route_success(self):
        response = self.client.get(f'/category/{MOCK_CAT_SLUG}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"RunCommands Tool", response.data)
        self.assertIn(b"Host to IP ", response.data) # Check Host2IP presence

    def test_category_route_not_found(self):
        response = self.client.get('/category/invalid-category-slug')
        self.assertEqual(response.status_code, 404)

    def test_tool_route_success(self):
        response = self.client.get(f'/tool/{MOCK_CAT_SLUG}/{MOCK_RUN_TOOL_SLUG}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"A tool that runs via commands.", response.data) # Description
        self.assertIn(b"runtool --execute", response.data) # Run command visible

    def test_tool_route_not_found(self):
        response = self.client.get(f'/tool/{MOCK_CAT_SLUG}/invalid-tool-slug')
        self.assertEqual(response.status_code, 404)
        response = self.client.get(f'/tool/invalid-cat-slug/{MOCK_RUN_TOOL_SLUG}')
        self.assertEqual(response.status_code, 404)

    # --- RUN_COMMANDS Execution Tests ---
    @patch('webapp.app.subprocess.Popen')
    def test_run_commands_tool_success(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'Successful command output', b'')
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        response = self.client.get(f'/run_tool/{MOCK_CAT_SLUG}/{MOCK_RUN_TOOL_SLUG}') # GET, not POST
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tool executed successfully.", response.data)
        self.assertIn(b"Successful command output", response.data)
        mock_popen.assert_called_once_with(
            "runtool --execute", # The command from mock data
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=project_root # Expect CWD to be project root
        )

    @patch('webapp.app.subprocess.Popen')
    def test_run_commands_tool_failure(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'Output on stdout', b'Error on stderr')
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        response = self.client.get(f'/run_tool/{MOCK_CAT_SLUG}/{MOCK_RUN_TOOL_SLUG}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tool execution completed with errors", response.data)
        self.assertIn(b"Output on stdout", response.data)
        self.assertIn(b"STDERR: Error on stderr", response.data)
        self.assertIn(b"Command exited with error code: 1", response.data)

    # --- Custom Tool Execution Tests ---

    # For Host2IP, we mock the class's run method for simplicity,
    # as testing sys.stdin/stdout redirection within a Flask test is complex.
    @patch('webapp.app.Host2IP') # Mock the class where it's imported in webapp.app
    def test_run_host2ip_tool(self, MockHost2IPClass):
        # Configure the mock instance and its run method
        mock_host2ip_instance = MockHost2IPClass.return_value
        
        # Simulate Host2IP.run() behavior:
        # It normally prints to sys.stdout. We need to capture that.
        # The route itself redirects sys.stdout to a StringIO.
        # So, we just need the mock_host2ip_instance.run() to be callable.
        # The route will capture what would have been printed.
        
        # To simulate output, we can make the mocked run() write to the captured_stdout
        # that webapp.app.run_custom_tool_view sets up.
        # This requires webapp.app.sys.stdout to be the StringIO at the time run() is called.
        # The actual redirection is done in the route, so we don't need to mock sys here in the test method itself for this strategy.
        
        # Let's verify the route handler correctly uses the mocked instance's run()
        # and captures what it would print.
        
        # For this test, we'll assume Host2IP().run() would print "IP_ADDRESS_FOR_EXAMPLE.COM"
        # when it's called, and the route's redirection of sys.stdout will capture it.
        # The actual Host2IP().run() uses input() then print().
        # The route redirects sys.stdin with the form data.
        # So, Host2IP().run() will get 'example.com' via its input().
        # Then it will call socket.gethostbyname('example.com').
        # Let's mock socket.gethostbyname to control the output.
        
        with patch('socket.gethostbyname') as mock_gethostbyname:
            mock_gethostbyname.return_value = "123.123.123.123" # Mocked IP

            response = self.client.post(
                f'/run_custom_tool/{MOCK_CAT_SLUG}/{MOCK_HOST2IP_SLUG}',
                data={'host_name': 'example.com'}
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"123.123.123.123", response.data) # Check for mocked IP
            self.assertIn(b"Tool executed successfully.", response.data) # Should be successful
            # Verify that the mocked Host2IP class was instantiated
            MockHost2IPClass.assert_called_once()
            # Verify its run method was called
            mock_host2ip_instance.run.assert_called_once()


    @patch('webapp.app.subprocess.Popen')
    def test_run_striker_tool_success(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'Striker scan complete', b'')
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        response = self.client.post(
            f'/run_custom_tool/{MOCK_CAT_SLUG}/{MOCK_STRIKER_SLUG}',
            data={'site_name': 'example.com'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tool executed successfully.", response.data)
        self.assertIn(b"Striker scan complete", response.data)
        
        expected_striker_dir = os.path.join(project_root, "Striker")
        mock_popen.assert_called_once_with(
            ["sudo", "python3", "striker.py", "example.com"],
            cwd=expected_striker_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    @patch('webapp.app.subprocess.Popen')
    def test_run_striker_tool_failure(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'Striker error')
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        response = self.client.post(
            f'/run_custom_tool/{MOCK_CAT_SLUG}/{MOCK_STRIKER_SLUG}',
            data={'site_name': 'example.com'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tool execution completed with errors", response.data)
        self.assertIn(b"STDERR: Striker error", response.data)
        self.assertIn(b"Striker exited with error code: 1", response.data)

    @patch('webapp.app.subprocess.Popen')
    def test_run_striker_tool_script_not_found(self, mock_popen):
        # This test assumes Striker dir/script might be missing
        # We need to make os.path.isdir or os.path.isfile return False for the Striker path
        with patch('os.path.isdir', return_value=False): # Or patch os.path.isfile for striker.py
            response = self.client.post(
                f'/run_custom_tool/{MOCK_CAT_SLUG}/{MOCK_STRIKER_SLUG}',
                data={'site_name': 'example.com'}
            )
            self.assertEqual(response.status_code, 200) # Route still returns 200 but with error message
            self.assertIn(b"Error: Striker directory or script not found", response.data)
            mock_popen.assert_not_called() # Popen should not be called if script is not found


if __name__ == '__main__':
    unittest.main()

# Placeholder for subprocess if needed directly by tests, not just for mocking webapp.app.subprocess
import subprocess
