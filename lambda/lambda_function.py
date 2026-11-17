import boto3
import csv
import json
from io import StringIO
from urllib.parse import unquote_plus

s3 = boto3.client("s3")

INPUT_BUCKET = "bld-tseed-workshop-input-semillero-2026-q4-c"
INPUT_KEY = "Santiago_Jaimes/users_dataset_100.csv"

OUTPUT_BUCKET = "bld-tseed-workshop-output-semillero-2026-q4-c"
OUTPUT_PREFIX = "Santiago_Jaimes/users_json/"


def split_csv_list(value):
    """
    Convierte un valor como:
    'C++, Project Management, Data Analysis'

    En:
    ['C++', 'Project Management', 'Data Analysis']
    """
    if not value:
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def transform_user(row):
    """
    Convierte los valores del CSV a tipos de datos apropiados
    para el archivo JSON.
    """
    return {
        "user_id": int(row["user_id"]),
        "name": row["name"].strip(),
        "country": row["country"].strip(),
        "city": row["city"].strip(),
        "role": row["role"].strip(),
        "department": row["department"].strip(),
        "education": row["education"].strip(),
        "age": int(row["age"]),
        "gender": row["gender"].strip(),
        "marital_status": row["marital_status"].strip(),
        "experience_years": int(row["experience_years"]),
        "skills": split_csv_list(row["skills"]),
        "languages": split_csv_list(row["languages"]),
        "hobbies": split_csv_list(row["hobbies"]),
        "salary": float(row["salary"]),
        "email": row["email"].strip(),
        "phone": row["phone"].strip()
    }


def get_input_location(event):
    """
    Si la Lambda fue activada por un evento de S3,
    obtiene el bucket y la ruta desde el evento.

    Si la Lambda se ejecuta manualmente desde la consola,
    utiliza el bucket y el archivo configurados arriba.
    """
    if event.get("Records"):
        record = event["Records"][0]

        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])

        return bucket, key

    return INPUT_BUCKET, INPUT_KEY


def lambda_handler(event, context):
    input_bucket, input_key = get_input_location(event)

    # Evita procesar archivos diferentes al CSV esperado.
    if input_bucket != INPUT_BUCKET:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "El evento proviene de un bucket no permitido.",
                "bucket": input_bucket
            })
        }

    if input_key != INPUT_KEY:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "El archivo no corresponde al CSV esperado.",
                "key": input_key
            })
        }

    try:
        response = s3.get_object(
            Bucket=input_bucket,
            Key=input_key
        )

        csv_content = (
            response["Body"]
            .read()
            .decode("utf-8-sig")
        )

        reader = csv.DictReader(StringIO(csv_content))

        files_created = 0
        generated_files = []

        for row in reader:
            user = transform_user(row)
            user_id = user["user_id"]

            output_key = (
                f"{OUTPUT_PREFIX}"
                f"user_{user_id:03d}.json"
            )

            s3.put_object(
                Bucket=OUTPUT_BUCKET,
                Key=output_key,
                Body=json.dumps(user).encode("utf-8"),
                ContentType="application/json"
            )

            files_created += 1
            generated_files.append(output_key)

        result = {
            "message": "CSV procesado correctamente.",
            "input": {
                "bucket": input_bucket,
                "key": input_key
            },
            "output": {
                "bucket": OUTPUT_BUCKET,
                "prefix": OUTPUT_PREFIX
            },
            "files_created": files_created,
            "first_file": (
                generated_files[0]
                if generated_files
                else None
            ),
            "last_file": (
                generated_files[-1]
                if generated_files
                else None
            )
        }

        print(json.dumps(result, ensure_ascii=False))

        return {
            "statusCode": 200,
            "body": json.dumps(
                result,
                ensure_ascii=False
            )
        }

    except s3.exceptions.NoSuchKey:
        return {
            "statusCode": 404,
            "body": json.dumps({
                "message": "No se encontró el archivo CSV.",
                "bucket": input_bucket,
                "key": input_key
            })
        }

    except Exception as error:
        print(f"Error procesando el CSV: {str(error)}")

        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Ocurrió un error procesando el CSV.",
                "error": str(error)
            })
        }