# Base image
FROM python:3.9-buster

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV HACKINGTOOL_INSTALL_PATH=/opt/hackingtools_downloads
ENV FLASK_APP=webapp/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Set working directory
WORKDIR /opt/hackingtool_web_app

# Create directory for downloaded tools (used by hackingtool.py logic)
RUN mkdir -p $HACKINGTOOL_INSTALL_PATH

# Create hackingtoolpath.txt for the root user, as install.sh and some tools might run as root initially
# This ensures that if hackingtool.py's path logic is invoked, it uses our defined path.
RUN echo "$HACKINGTOOL_INSTALL_PATH" > /root/hackingtoolpath.txt

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    git \
    curl \
    procps \
    php-cli \
    nmap \
    default-jre \
    iputils-ping \
    net-tools \
    libpcap-dev \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    golang \
    figlet \
    boxes \
    xdotool \
    wget \
    # Dependencies for specific tools that might be missed by install.sh
    # e.g., for routersploit, commix, etc.
    # python3-venv is needed by install.sh
    python3-venv \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire repository content
COPY . .

# Install Python dependencies for the web application
RUN pip install --no-cache-dir -r webapp/requirements.txt

# Install Python dependencies for the hackingtool and its tools (root requirements)
# Some of these might be re-installed by install.sh in its venv, but good to have base ones.
RUN pip install --no-cache-dir -r requirements.txt

# Make install.sh executable and run it non-interactively for Debian-based systems
# The 'y' is to confirm replacement if /usr/share/hackingtool already exists (unlikely in clean build)
# The '1' is to choose the Debian/apt option in install.sh
RUN chmod +x install.sh \
    && echo -e "y\n" | ./install.sh 1

# Create a non-root user to run the application
RUN useradd -ms /bin/bash -G sudo appuser \
    && echo "appuser ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/appuser_nopasswd \
    && chmod 0440 /etc/sudoers.d/appuser_nopasswd

# Set the user for subsequent commands
USER appuser

# Re-create hackingtoolpath.txt for appuser in its home directory, pointing to the shared path
# This is if any tool run by appuser invokes the path logic from hackingtool.py
RUN mkdir -p $(dirname $HACKINGTOOL_INSTALL_PATH) && echo "$HACKINGTOOL_INSTALL_PATH" > /home/appuser/hackingtoolpath.txt

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the application
# The webapp is in a subdirectory, so Flask needs to find app.py
# FLASK_APP is already set. CWD will be /opt/hackingtool_web_app
CMD ["flask", "run"]
