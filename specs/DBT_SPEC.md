# dbt Specification

Create a proper dbt project.

Directories:
- models/staging
- models/intermediate
- models/marts
- tests
- macros where needed
- seeds only where useful

Required:
- source definitions
- staging models that clean/standardize raw data
- intermediate models for reusable transformations
- marts for business-facing analytics
- schema documentation
- generic tests
- custom tests for important business rules
- generated documentation configuration where practical

Business logic should live primarily in SQL/dbt rather than duplicated in Python.
