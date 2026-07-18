FROM public.ecr.aws/lambda/python:3.11

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# We explicitly install the CPU version of PyTorch to save space and since Lambda has no GPU
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# Copy function code and data
COPY . ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_handler.handler" ]
