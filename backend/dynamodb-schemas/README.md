# DynamoDB Schemas

This directory contains schema documentation for all DynamoDB tables used in the platform.

## Tables

### 1. `startup-investor-platform-dev-startups`
- **Purpose**: Stores all startup information
- **Schema**: [startups-table.json](./startups-table.json)
- **Key**: `startup_id` (String, Hash Key)
- **Indexes**: 
  - `IndustryIndex` - Query by industry
  - `FundingStageIndex` - Query by funding stage
- **TTL**: Enabled on `expiration_time`

### 2. `startup-investor-platform-dev-investors`
- **Purpose**: Stores investor profiles and preferences
- **Schema**: [investors-table.json](./investors-table.json)
- **Key**: `investor_id` (String, Hash Key)
- **Indexes**: None (single table design)

## Usage

These schemas serve as:
- **Documentation** - Reference for developers
- **Validation** - Ensure code matches expected structure
- **Onboarding** - Help new team members understand data model

## Notes

- Both tables use **PAY_PER_REQUEST** billing mode (serverless, auto-scaling)
- Tables are in `eu-north-1` region
- Environment prefix: `startup-investor-platform-dev-`

## Schema Updates

When updating table structures:
1. Update the JSON schema file
2. Update CloudFormation template
3. Document breaking changes
4. Plan migration if needed

