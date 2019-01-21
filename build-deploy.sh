sam build && \
sam package --s3-bucket dict-lambda-code --output-template-file packaged.yaml && \
aws cloudformation deploy --template-file /Users/rama/work/aws-dict-sam/packaged.yaml --stack-name dict-lambda-stack --capabilities CAPABILITY_IAM
