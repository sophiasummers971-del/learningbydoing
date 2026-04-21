# Contributing to HackingTool

Thank you for your interest in contributing! Please follow these guidelines.

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-tool`)
3. Add your tool to the appropriate category in `tools/`
4. Ensure your tool class has: TITLE, DESCRIPTION, INSTALL_COMMANDS, RUN_COMMANDS, SUPPORTED_OS
5. Test locally: `python hackingtool.py`
6. Commit your changes (`git commit -m 'Add amazing tool'`)
7. Push to the branch (`git push origin feature/amazing-tool`)
8. Open a Pull Request using the `[New Tool] ToolName — Category` format

## Tool Request

Open an issue with `[Tool Request] ToolName — Category` title format.

Required info: tool name, GitHub URL, category, OS, install command, reason.

## Code Style

- Python 3.10+
- Follow existing tool class structure
- Keep descriptions concise
- Test on Linux (Kali/Parrot preferred)

## Security

- Do NOT include actual exploit payloads in PRs
- Report security vulnerabilities privately via GitHub Security Advisories
- Tools must have legitimate security research/penetration testing purposes

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
