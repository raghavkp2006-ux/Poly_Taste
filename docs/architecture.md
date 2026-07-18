# Architecture Document

## Overview
This is a multi-module recommendation app built using FastAPI and AWS Serverless services to strictly adhere to the AWS Free Tier. It consists of three independent modules: Spotify, Anime, and Amazon.

## AWS Infrastructure
- **API Gateway**: HTTP API routing requests to the Lambda function.
- **Lambda**: A single AWS Lambda function running the FastAPI application via Mangum.
- **DynamoDB**: Used by the Spotify module to store user tokens (on-demand billing).
- **S3 Bucket**: Stores static datasets (JSON catalogs) for Anime and Amazon modules.
- **CloudWatch**: Logs from Lambda, and a custom dashboard for request metrics.
- **IAM**: Least-privilege roles for the Lambda function to access only the specific DynamoDB table and S3 bucket.

## Application Architecture
- **FastAPI**: The core web framework.
- **Jinja2**: Server-side rendering for the frontend.
- **Recommendation Engines**:
  - **Spotify**: Content-based similarity using Spotify audio features (danceability, energy, tempo, valence, acousticness).
  - **Anime & Amazon**: TF-IDF and cosine similarity on text fields (synopsis, genres, descriptions).

## Data Flow
- **Spotify**: Users authenticate via OAuth. Tokens are stored in DynamoDB. The app queries Spotify API on-the-fly and computes similarities.
- **Anime & Amazon**: Data is loaded from external sources (Jikan API, Kaggle) via offline/one-off scripts and saved to S3. Lambda caches this data in-memory at cold start and uses it to serve recommendations.
