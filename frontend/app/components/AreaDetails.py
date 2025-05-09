import streamlit as st
import pandas as pd

def AreaDetails(area_details, area_transactions):
    st.write("---")
    st.subheader("Détails de la Localité")
    st.write(area_details)
    st.write("---")
    st.subheader("Transactions Immobilières")
    st.write(area_transactions)

