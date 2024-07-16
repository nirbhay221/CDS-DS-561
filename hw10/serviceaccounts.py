def GenerateConfig(context):
    project_id = context.env['project']
    service_account = context.properties['service-account']

    resources = [
        {
            'name': service_account,
            'type': 'iam.v1.serviceAccount',
            'properties': {
                'accountId': service_account,
                'displayName': service_account,
                'projectId': project_id
            }
        },
        {
            'name': 'bind-iam-policy',
            'type': 'gcp-types/cloudresourcemanager-v1:virtual.projects.iamMemberBinding',
            'properties': {
                'resource': project_id,
                'role': 'roles/dataflow.admin',
                'member': 'serviceAccount:$(ref.' + service_account + '.email)'
            },
            'metadata': {
                'dependsOn': [service_account]
            }
        },
        {
            'name': 'storage-admin-binding',
            'type': 'gcp-types/cloudresourcemanager-v1:virtual.projects.iamMemberBinding',
            'properties': {
                'resource': project_id,
                'role': 'roles/storage.admin',
                'member': 'serviceAccount:$(ref.' + service_account + '.email)'
            },
            'metadata': {
                'dependsOn': [service_account]
            }
        },
        {
            'name': 'object-admin-binding',
            'type': 'gcp-types/cloudresourcemanager-v1:virtual.projects.iamMemberBinding',
            'properties': {
                'resource': project_id,
                'role': 'roles/storage.objectAdmin',
                'member': 'serviceAccount:$(ref.' + service_account + '.email)'
            },
            'metadata': {
                'dependsOn': [service_account]
            }
        },
        {
            'name': 'cloud-sql-admin-binding',
            'type': 'gcp-types/cloudresourcemanager-v1:virtual.projects.iamMemberBinding',
            'properties': {
                'resource': project_id,
                'role': 'roles/cloudsql.admin',
                'member': 'serviceAccount:$(ref.' + service_account + '.email)'
            },
            'metadata': {
                'dependsOn': [service_account]
            }
        },
        {
            'name': 'logging-admin-binding',
            'type': 'gcp-types/cloudresourcemanager-v1:virtual.projects.iamMemberBinding',
            'properties': {
                'resource': project_id,
                'role': 'roles/logging.admin',
                'member': 'serviceAccount:$(ref.' + service_account + '.email)'
            },
            'metadata': {
                'dependsOn': [service_account]
            }
        }
    ]

    return {'resources': resources}