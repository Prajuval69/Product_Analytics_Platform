# Environment Guidance

Use environment variables for database connection settings and other runtime configuration.

Provide `.env.example` in the generated project, but never commit real credentials.

The preferred local experience is Docker Compose for PostgreSQL and Airflow. The Python/dbt project should remain understandable outside Docker as well.
