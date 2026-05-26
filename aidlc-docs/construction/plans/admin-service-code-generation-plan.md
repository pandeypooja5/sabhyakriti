# Code Generation Plan — Unit 7: Admin Microservice
# sabhyakriti-admin-service

## Unit Context
| Repository | `sabhyakriti-admin-service` | Port 8007 |
| No DB | Pure aggregation BFF — no SQLAlchemy, no Alembic |
| Requirements | FR-ADM-01 to FR-ADM-11 |
| Depends on | All Units 1-6 (aggregates from all services) |

## Steps
- [x] 1: Project setup (no DB deps — no sqlalchemy/asyncpg/alembic in requirements)
- [x] 2: Application DTOs (DashboardDTO, SalesReportDTO, CustomerSummaryDTO, CustomerDetailDTO)
- [x] 3: Service clients (OrderClient, ProductClient, AuthClient, CartClient — all httpx async)
- [x] 4: AdminApplicationService (dashboard KPIs, sales report, customer list/detail)
- [x] 5: Presentation (dependencies with JWT+admin check, all routers, main.py)
- [x] 6: Tests (mock all service clients; test aggregation logic, partial-failure handling)
- [x] 7: Documentation
