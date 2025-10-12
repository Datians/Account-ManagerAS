from sqlalchemy import or_
def apply_search(query, model, term:str, columns):
    if not term:
        return query
    like = f"%{term.strip()}%"
    conditions = [getattr(model, col).ilike(like) for col in columns]
    return query.filter(or_(*conditions))
