# SWMS Generator — Mobile Web App

Phone-first Streamlit app for populating the supplied Sky5 SWMS PR004 PDF template.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL shown by Streamlit. On an iPhone, open the same URL in Safari if the computer and phone are on the same Wi-Fi network.

## Put it online

The easiest deployment is Streamlit Community Cloud:

1. Create a GitHub repository.
2. Upload `app.py`, `swms_engine.py`, `template.pdf`, `requirements.txt`, and `.streamlit/config.toml`.
3. In Streamlit Community Cloud, create a new app and select the repository.
4. Set the main file to `app.py`.
5. Deploy.
6. Open the resulting web address on your iPhone in Safari.
7. Safari → Share → Add to Home Screen.

No API key or database is required for this version.

## Important

The app is a form/population tool. It does not determine whether work is safe. A competent person must review site conditions, hazards, controls, permits, rescue arrangements and the final SWMS before work starts.
