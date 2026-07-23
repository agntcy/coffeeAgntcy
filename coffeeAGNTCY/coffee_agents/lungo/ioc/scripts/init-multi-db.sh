#!/bin/bash
set -e

# Create the additional databases needed by the IoC management and CFN services.
# Runs inside the ioc-knowledge-memory-svc-db container on first init only.
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
	CREATE DATABASE cfn_mgmt;
	CREATE DATABASE cfn_cp;
EOSQL

echo "Databases 'cfn_mgmt' and 'cfn_cp' created successfully"
