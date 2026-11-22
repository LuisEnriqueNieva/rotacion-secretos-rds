import boto3
import pymysql
import secrets
import string

AMBIENTES = ['dev', 'test', 'prod']

def generar_password(longitud=16):
    caracteres = string.ascii_letters + string.digits + '-_@#%'
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

def lambda_handler(event, context):
    ssm = boto3.client('ssm')
    host = ssm.get_parameter(
        Name='/rds_mysql_alumnos/punto_enlace',
        WithDecryption=True
    )['Parameter']['Value']
    admin_password = ssm.get_parameter(
        Name='/rds_mysql_alumnos/admin/password',
        WithDecryption=True
    )['Parameter']['Value']

    connection = pymysql.connect(
        host=host,
        user='admin',
        password=admin_password,
        connect_timeout=5
    )

    rotados = []
    try:
        with connection.cursor() as cursor:
            for ambiente in AMBIENTES:
                usuario = 'user_' + ambiente
                nuevo_password = generar_password()
                cursor.execute(
                    "ALTER USER %s IDENTIFIED BY %s",
                    (usuario, nuevo_password)
                )
                ssm.put_parameter(
                    Name='/rds_mysql_alumnos/' + usuario + '/password',
                    Value=nuevo_password,
                    Type='SecureString',
                    Overwrite=True
                )
                rotados.append(usuario)
            cursor.execute("FLUSH PRIVILEGES")
        connection.commit()
    finally:
        connection.close()

    print("Passwords rotados para:", rotados)
    return {
        "statusCode": 200,
        "rotados": rotados
    }
