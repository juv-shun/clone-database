import json
import logging
import pathlib

import boto3

rdsclient = boto3.client("rds")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_latest_snapshot(db_instance):
    snapshots = rdsclient.describe_db_snapshots(
        DBInstanceIdentifier=db_instance,
        SnapshotType='automated',
    )
    return sorted(
        snapshots["DBSnapshots"],
        key=lambda x: x['SnapshotCreateTime'],
        reverse=True,
    )[0]['DBSnapshotIdentifier']


def run_genral_instance(snapshot_id, db_name, instance_class, az, storage_type, subnet_group, parameter_group, engine):
    rdsclient.restore_db_instance_from_db_snapshot(
        DBSnapshotIdentifier=snapshot_id,
        DBInstanceIdentifier=db_name,
        DBInstanceClass=instance_class,
        AvailabilityZone=az,
        PubliclyAccessible=False,
        StorageType=storage_type,
        DBSubnetGroupName=subnet_group,
        DBParameterGroupName=parameter_group,
        MultiAZ=False,
        Engine='MySQL',
        Tags=[
            {
                'Key': 'DELETABLE',
                'Value': 'true'
            },
        ]
    )


def run_aurora_cluster(identifiler, db_name, port, subnet_group):
    # cloneの作成
    rdsclient.restore_db_cluster_to_point_in_time(
        DBClusterIdentifier=db_name,
        RestoreType='copy-on-write',
        SourceDBClusterIdentifier=identifiler,
        Port=port,
        UseLatestRestorableTime=True,
        DBSubnetGroupName=subnet_group,
        Tags=[
            {
                'Key': 'DELETABLE',
                'Value': 'true'
            },
        ],
        EnableIAMDatabaseAuthentication=False
    )


def run_aurora_instance(db_name, instance_class, az, subnet_group, parameter_group):
    rdsclient.create_db_instance(
        DBClusterIdentifier=db_name,
        DBInstanceIdentifier=db_name,
        DBInstanceClass=instance_class,
        Engine='aurora',
        AvailabilityZone=az,
        DBSubnetGroupName=subnet_group,
        DBParameterGroupName=parameter_group,
        MultiAZ=False,
        Tags=[
            {
                'Key': 'DELETABLE',
                'Value': 'true'
            },
        ]
    )


def handle(event, context):
    with open(pathlib.Path(__file__).parent / "databases.json", "rt") as f:
        target_dbs = json.load(f)

    for db in target_dbs:
        if db["type"] == "general":
            snapshot_id = get_latest_snapshot(db["Identifier"])
            dt = "-".join(snapshot_id.split("-")[-5:-2])
            db_name = f"clone-{db['Identifier']}-{dt}"
            run_genral_instance(snapshot_id, db_name, **db["settings"])
            logger.info(f'clone DB for {db["Identifier"]} has been started.')
        elif db["type"] == "aurora":
            db_name = f"clone-{db['Identifier']}-{dt}"
            run_aurora_cluster(db["Identifier"], db_name, **db["cluster_settings"])
            logger.info(f"cluster for {db['Identifier']} has been started.")
            run_aurora_instance(db_name, **db["instance_settings"])
            logger.info(f"instance for {db['Identifier']} has been started.")

    return "OK"
