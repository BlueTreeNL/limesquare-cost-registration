import streamlit as st
import pandas as pd
import psycopg2
import time

pd.set_option("display.float_format", "{:.2f}".format)


def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])


def run_select_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def run_insert_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()


st.set_page_config(page_title="Kosten registratie", page_icon="💸", layout="centered")

conn = init_connection()
amount_value = 0

st.title("💸 Kosten registratie")

projects = run_select_query(
    "SELECT projects.name, organizations.name, project_id FROM projects LEFT JOIN organizations ON organizations.organization_id = projects.organization_client_id"
)
project_ids = (project for project in projects)

form = st.form(key="annotation")

with form:
    project = st.selectbox("Project:", project_ids)

    cols = st.columns(3)
    date = cols[0].date_input("Datum:")
    amount = cols[1].number_input("Bedrag:", step=1, value=amount_value)
    invoiced = cols[2].radio("Gefactureerd:", ("Ja", "Nee"))

    submitted = st.form_submit_button(label="Verstuur")

if submitted:
    sql_invoiced = True if invoiced == "Ja" else False
    project_id = project[2]
    run_insert_query(
        f"INSERT INTO manual_costs(project_id, date, amount, invoiced) VALUES ('{ project_id }', '{ date }', { amount }, {sql_invoiced}) ON CONFLICT (project_id, date) DO UPDATE SET amount={ amount }, invoiced={ sql_invoiced } WHERE manual_costs.project_id = '{ project_id }' AND manual_costs.date = '{ date }'"
    )
    st.success("De kosten zijn geregistreerd!")
    st.balloons()

with st.expander("Bekijk een overzicht van de geregistreerde kosten"):
    df = pd.DataFrame(
        run_select_query(
            "SELECT projects.name, organizations.name, projects.project_id, date, amount, invoiced FROM manual_costs LEFT JOIN projects ON projects.project_id = manual_costs.project_id LEFT JOIN organizations ON organizations.organization_id = projects.organization_client_id WHERE amount != 0"
        ),
        columns=["Project", "Organisatie", "Project ID", "Datum", "Bedrag", "Gefactureerd"],
    )
    df = df.astype({"Bedrag": "int"})
    st.dataframe(df)
