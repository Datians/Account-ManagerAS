import pandas as pd

COLUMNS = ['platform','username','password','provider','client','start_date','end_date','time_allocated','notes']

def generate_template_bytes():
    import io
    df = pd.DataFrame(columns=COLUMNS)
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Cuentas')
    bio.seek(0)
    return bio
