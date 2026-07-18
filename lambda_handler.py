from mangum import Mangum
from main import app

# This acts as the entry point for AWS Lambda
handler = Mangum(app)
