import streamlit as st

# Mettre la page en très large
st.set_page_config(layout="wide")

st.title("A propos ℹ️")

st.markdown("""
Cette application permet de visualiser les prix immobiliers en France, ainsi que les sentiments associés aux différentes localités.
Elle utilise les données de la base de données [Base Adresse Nationale (BAN)](https://adresse.data.gouv.fr/), ainsi que les données de [data.gouv.fr](https://www.data.gouv.fr/).
""")

st.markdown("""
Ce projet a été réalisé par :
- [Nicolas Delplanque](https://github.com/ndevplanque)
- [Thibaut Ruscher](https://github.com/ThibautRuscher)
- [Safidy Joas](https://github.com/Razanakotoniaina)
- [Pierre Halm](https://github.com/Pirooooooo)
""")
