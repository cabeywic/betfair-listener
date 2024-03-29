FROM python:latest

# Set the working directory to /usr/app/src
WORKDIR /usr/app/

# Copy the requirements file to the working directory.
COPY requirements.txt /usr/app/

# Install dependencies.
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /usr/app/src
COPY . /usr/app/

RUN mkdir /usr/logs

# Run the app.
CMD [ "python", "src/main.py", "-f"]