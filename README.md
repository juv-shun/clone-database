## Overview
This is a lambda application to clone database on RDS created by serverless application.

## Structure
This application is constructed by two lambda functions, `planter` and `harvester`.

### planter
`planter` function is invoked every morning.
It runs RDS instances by their latest snapshot.
Only databases described in `databases.json` are cloned.

### harvester
`harverster` function is invoked every morning.
It deletes clone RDS instances generated before today.
