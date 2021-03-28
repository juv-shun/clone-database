import logging
from datetime import date, timedelta

import boto3

rdsclient = boto3.client("rds")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def is_deletable(db):
    try:
        dt = date(*[int(n) for n in db['DBInstanceIdentifier'].split('-')[-3:]])
    except Exception:
        return False

    if dt == date.today() - timedelta(days=1):
        return False

    for tag in db['TagList']:
        if tag['Key'] == 'DELETABLE' and tag['Value'] == 'true':
            return True

    return False


def handle(event, context):
    databases = rdsclient.describe_db_instances(MaxRecords=100)['DBInstances']
    for db in databases:
        if not is_deletable(db):
            continue

        rdsclient.delete_db_instance(
            DBInstanceIdentifier=db['DBInstanceIdentifier'],
            SkipFinalSnapshot=True,
        )
        logger.info(f"DB instance {db['DBInstanceIdentifier']} successfully deleted.")

        if db['Engine'] == 'aurora':
            rdsclient.delete_db_cluster(
                DBClusterIdentifier=db['DBClusterIdentifier'],
                SkipFinalSnapshot=True,
            )
            logger.info(f"DB cluster {db['DBClusterIdentifier']} successfully deleted.")
