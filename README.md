# Taller HandsOnLab1 – Santiago Jaimes

Pipeline de datos en AWS donde se lee un archivo CSV desde Amazon S3, se transforma cada registro en un archivo JSON mediante AWS Lambda, se cataloga con AWS Glue y finalmente se consulta utilizando SQL en Amazon Athena.

```text
S3 (input: CSV)
        │
        ▼
AWS Lambda (CSV → JSON)
        │
        ▼
S3 (output: JSON)
        │
        ▼
Glue Crawler (Data Catalog)
        │
        ▼
Amazon Athena (SQL)
```

---

# 1. Lambda: de CSV a JSON

Se creó la función Lambda **bld-tseed-workshop-santiago-jaimes** para leer el archivo:

```text
s3://bld-tseed-workshop-input-semillero-2026-q4-c/
└── Santiago_Jaimes/
    └── users_dataset_100.csv
```

La función procesa cada fila del CSV y genera un archivo JSON independiente utilizando el campo `user_id` como identificador.

Los archivos son almacenados en:

```text
s3://bld-tseed-workshop-output-semillero-2026-q4-c/
└── Santiago_Jaimes/
    └── users_json/
```

Código:

```text
lambda/lambda_function.py
```

## Ejemplo de registro generado

Archivo:

```text
user_010.json
```

Contenido:

```json
{"user_id":10,"name":"Joseph Brown","country":"Italy","city":"Port Lisa","role":"Engineer","department":"HR","education":"Master","age":47,"gender":"Male","marital_status":"Married","experience_years":16,"skills":["Python","Excel","SQL"],"languages":["English"],"hobbies":["Reading","Sports"],"salary":84553.43,"email":"example@email.com","phone":"123456789"}
```

Para evitar errores de lectura en Athena, los JSON se almacenan en una sola línea utilizando:

```python
json.dumps(
    user,
    ensure_ascii=False,
    separators=(",", ":")
)
```

## Permisos

Se agregó una política al rol de ejecución de Lambda con permisos:

### Lectura

```json
s3:GetObject
```

sobre:

```text
bld-tseed-workshop-input-semillero-2026-q4-c/Santiago_Jaimes/*
```

### Escritura

```json
s3:PutObject
```

sobre:

```text
bld-tseed-workshop-output-semillero-2026-q4-c/Santiago_Jaimes/*
```

## Resultado

La ejecución de la función generó:

```text
100 archivos JSON
```

dentro de:

```text
Santiago_Jaimes/users_json/
```

---

# 2. Glue: catálogo de datos

Se creó la base de datos:

```text
bld-tseed-workshop-santiago-jaimes
```

Posteriormente se creó un crawler configurado en modo **On Demand** apuntando a:

```text
s3://bld-tseed-workshop-output-semillero-2026-q4-c/Santiago_Jaimes/users_json/
```

Al ejecutarse, el crawler creó automáticamente la tabla:

```text
users_json
```

con clasificación:

```text
json
```

y detectó correctamente los tipos de datos.

## Esquema generado

```text
user_id             int
name                string
country             string
city                string
role                string
department          string
education           string
age                 int
gender              string
marital_status      string
experience_years    int
skills              array<string>
languages           array<string>
hobbies             array<string>
salary              double
email               string
phone               string
```

---

# 3. Athena: consultas SQL

## Cómo se ejecutaron

1. En Amazon Athena se configuró una ubicación para almacenar los resultados de las consultas.

```text
s3://bld-tseed-workshop-output-semillero-2026-q4-c/Santiago_Jaimes/athena-results/
```

2. Se utilizó el catálogo:

```text
AwsDataCatalog
```

3. Se seleccionó la base de datos:

```text
bld-tseed-workshop-santiago-jaimes
```

4. Las consultas se ejecutaron desde el Query Editor utilizando:

```text
Run
```

o

```text
Ctrl + Enter
```

5. Los resultados fueron descargados en formato CSV desde el panel de resultados.

---

## Consulta 1: vista general de la tabla

Permite validar que Athena puede leer correctamente todos los archivos JSON catalogados por Glue.

```sql
SELECT *
FROM "AwsDataCatalog"."bld-tseed-workshop-santiago-jaimes"."users_json"
LIMIT 20;
```

Resultado:

```text
20 registros de muestra obtenidos correctamente.
```

Archivo:

```text
consulta1_general.csv
```

---

## Consulta 2: usuarios mayores de 35 años que hablan inglés

En este caso la columna `languages` fue detectada como:

```text
array<string>
```

por lo que se utiliza la función `contains()`.

```sql
SELECT
    user_id,
    name,
    age,
    country,
    languages
FROM "AwsDataCatalog"."bld-tseed-workshop-santiago-jaimes"."users_json"
WHERE age > 35
    AND contains(languages, 'English')
ORDER BY age DESC;
```

Resultado:

```text
26 resigtros de Usuarios que hablan inglés y tienen más de 35 años.
```

Archivo:

```text
consulta2_ingles_mayores_35.csv
```

---

## Consulta 3: empleados de IT y Finance con salario superior a 80.000

Esta consulta permite combinar filtros numéricos y categóricos.

```sql
SELECT
    user_id,
    name,
    department,
    salary
FROM "AwsDataCatalog"."bld-tseed-workshop-santiago-jaimes"."users_json"
WHERE department IN ('IT', 'Finance')
    AND salary > 80000
ORDER BY salary DESC;
```

Resultado:

```text
14 Registros de Empleados de IT y Finance con los salarios más altos.
```

Archivo:

```text
consulta3_it_finance_salario.csv
```



---

# Estructura del repositorio

```text
s2026q4c-hol1-sjaimes
│
├── README.md
│
├── lambda
│   └── lambda_function.py
│
├── csv-json
│   ├── user_001.json
│   ├── user_059.json
│   ├── consulta1_general.csv
│   ├── consulta2_ingles_mayores_35.csv
│   └── consulta3_it_finance_salario.csv
│
└── imagenes
    ├── 01_s3_input.png
    ├── 02_s3_output.png
    ├── 03_lambda.png
    ├── 04_Ejecutar_Test.png
    ├── 05_Datos_Cargados.png
    ├── 06_glue_catalog.png
    ├── 07_athena_query.png
    └── 08_query_results.png
```