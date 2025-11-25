# from fastapi import FastAPI, Header, HTTPException, Depends
# from library_management_api.modules.routes.books import router as books_router
# from library_management_api.modules.routes.loans import router as loans_router
# from library_management_api.modules.routes.reports import router as reports_router

# app = FastAPI(title="Sentiment Analysis")

# def get_auth(
#     x_role: str = Header(..., alias="X-Role"),
#     x_user_id: str | None = Header(None, alias="X-User-Id"),
# ):
#     if x_role not in {"admin", "student"}:
#         raise HTTPException(403, "X-Role harus 'admin' atau 'student'")
#     return {"role": x_role, "user_id": x_user_id}

# @app.get("/", include_in_schema=False)
# def root():
#     return {"ok": True}

# app.include_router(books_router, dependencies=[Depends(get_auth)])
# app.include_router(loans_router, dependencies=[Depends(get_auth)])
# app.include_router(reports_router, dependencies=[Depends(get_auth)])