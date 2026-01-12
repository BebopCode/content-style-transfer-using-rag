FROM python:3.11-slim

WORKDIR /app

# Build arguments with defaults
ARG NUMBER_OF_SAMPLE_EMAILS=2
ARG GENERATOR_MODEL_NAME=ministral
ARG RETRIEVED_EMAILS=5
ARG EVALUATOR_MODEL_NAME=ministral-3:8b
ARG BASE_URL=http://localhost:11434

# Convert to environment variables (available at runtime)
ENV NUMBER_OF_SAMPLE_EMAILS=${NUMBER_OF_SAMPLE_EMAILS}
ENV GENERATOR_MODEL_NAME=${GENERATOR_MODEL_NAME}
ENV RETRIEVED_EMAILS=${RETRIEVED_EMAILS}
ENV EVALUATOR_MODEL_NAME=${EVALUATOR_MODEL_NAME}
ENV BASE_URL=${BASE_URL}

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gdown
RUN python -m spacy download en_core_web_sm

# Copy your code into experiments/ directory
COPY . ./experiments/

# Download dataset from Google Drive (skip if already exists)
RUN gdown --id 1wTbb7J4O20hZFmyMTpntFLQ0-zt_eaEX -O experiments/emails_cleaned.csv

# Create entrypoint script
RUN echo '#!/bin/bash\n\
python -m experiments.enron\n\
python -m experiments.pipeline --limit $NUMBER_OF_SAMPLE_EMAILS --model-name $GENERATOR_MODEL_NAME --number-of-emails $RETRIEVED_EMAILS --base-url $BASE_URL\n\
python -m experiments.evaluator --model-name $EVALUATOR_MODEL_NAME --base-url $BASE_URL' > /app/entrypoint.sh \
&& chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]