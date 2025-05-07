# Use the official Python image
FROM python:3

# Set the working directory
WORKDIR /app

# Install Poetry globally
RUN pip install --no-cache-dir poetry && \
    rm -rf /root/.cache/pip

# Install build essentials for Rust compilation
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    curl \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Rust for Python package compilation
RUN curl --proto '=https' -sSf https://sh.rustup.rs | sh -s -- -y && \
    rm -rf /root/.rustup/toolchains/*/share/doc
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy the dependencies file to the working directory
COPY poetry.lock pyproject.toml ./

# Configure Poetry to use a local virtual environment and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

# Copy the content of the local app directory to the working directory
COPY . /app

# Add the working directory to PYTHONPATH
ENV PYTHONPATH=/app

# Expose the port the app runs on
EXPOSE 8125

# Command to run on container start
CMD ["python", "supervisor/main.py", "--server"]