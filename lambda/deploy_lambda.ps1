# deploy_lambda.ps1

$ROLE_ARN    = "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/LabRole"
$BUCKET      = "infrastucture-vbenitezz-dfsanchezv"
$SUBNET_1    = "subnet-0d36840cae3c847b3"
$SUBNET_2    = "subnet-0e978a63f7818da75"
$SG          = "sg-0435c675bc890383c"
$REGION      = "us-east-1"
$FUNC_NAME   = "prometheus-metrics-collector"

# 1. Empaquetar
Write-Host "Empaquetando Lambda..."
Compress-Archive -Path lambda_function.py -DestinationPath function.zip -Force

# 2. Crear o actualizar la función
$exists = aws lambda get-function --function-name $FUNC_NAME --region $REGION 2>$null
if ($exists) {
    Write-Host "Actualizando Lambda existente..."
    aws lambda update-function-code `
        --function-name $FUNC_NAME `
        --zip-file fileb://function.zip `
        --region $REGION
} else {
    Write-Host "Creando Lambda..."
    aws lambda create-function `
        --function-name $FUNC_NAME `
        --runtime python3.12 `
        --role $ROLE_ARN `
        --handler lambda_function.lambda_handler `
        --zip-file fileb://function.zip `
        --timeout 60 `
        --memory-size 256 `
        --vpc-config "SubnetIds=$SUBNET_1,$SUBNET_2,SecurityGroupIds=$SG" `
        --region $REGION
}

Write-Host "Listo. Lambda desplegada."