import os
import streamlit as st

# Path to your folder
BASE_FOLDER = r"C://Users//aksml//Development//Hardware//Avishkar//DSU_Final//public"

st.set_page_config(page_title="Sparsh Drishti", layout="wide")

def main():
    st.title("Sparsh Drishti")
    st.sidebar.image("logo.png", use_column_width=True)

    if "page" not in st.session_state:
        st.session_state.page = 0

    if st.session_state.page == 0:
        st.header("Welcome! Please enter your details.")
        name = st.text_input("Enter your Name")
        device_id = st.text_input("Enter your Device ID")

        if st.button("Submit"):
            if name and device_id:
                st.session_state.name = name
                st.session_state.device_id = device_id
                st.session_state.page = 1
            else:
                st.error("Please provide both Name and Device ID.")

    elif st.session_state.page == 1:
        with st.sidebar:
            st.title(f"Hello, {st.session_state.name}")
            option = st.radio(
                "Navigation",
                options=["Home", "Live Location", "Search", "Contact Us"],
                index=0,
            )

        if option == "Home":
            st.header("Welcome to Sparsh Drishti")
            st.write("This is a support system designed to assist blind people with various features.")
            st.markdown("""
                **India's Blind and Visually Impaired Population:**
                - There are an estimated 4.95 million people blind (0.36% of the total population).
                - 35 million people are visually impaired (2.55% of the population).
                - Approximately 0.24 million blind children are in India.
            """)

        elif option == "Live Location":
            st.header("Live Location")
            st.write("Below is the live map view of your location.")
            # google_maps_url = "https://maps.google.com/maps?q=12.9715987,77.594566&t=&z=13&ie=UTF8&iwloc=&output=embed"
            google_maps_url = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3889.2784351290848!2d77.54834101144367!3d12.889809287365605!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3bae3eecdc883cc1%3A0x1d44e022ac75925a!2sCity%20Engineering%20College!5e0!3m2!1sen!2sin!4v1732861092297!5m2!1sen!2sin"         
            st.markdown(
                f'<iframe src="{google_maps_url}" width="800" height="600" frameborder="0" style="border:0;" allowfullscreen></iframe>',
                unsafe_allow_html=True,
            )

        elif option == "Search":
            st.header("Search Files")
            st.write("Below are the files available for IDs ranging from 101 to 999:")

            try:
                # Get all files in the directory
                files = os.listdir(BASE_FOLDER)
                files.sort()

                # Define ID range and categorize files
                id_range = range(101, 1000)
                id_files = {str(i): [] for i in reversed(id_range)}  # Reverse the ID order

                for file in files:
                    file_id, ext = os.path.splitext(file)
                    if file_id.isdigit() and int(file_id) in id_range:
                        id_files[file_id].append(file)

                # Display files and interactive elements
                for file_id, file_list in id_files.items():
                    if file_list:  # Only display if files exist for the ID
                        st.subheader(f"Files for ID: {file_id}")
                        for file_name in file_list:
                            file_path = os.path.join(BASE_FOLDER, file_name)
                            ext = os.path.splitext(file_name)[-1].lower()

                            # Display content based on file type
                            if ext in [".jpg", ".png", ".jpeg"]:  # Image
                                st.image(file_path, caption=file_name, use_column_width=True)
                            elif ext == ".txt":  # Text
                                with open(file_path, "r") as f:
                                    st.text_area(label=file_name, value=f.read(), height=200)
                            elif ext == ".mp3":  # Audio
                                st.audio(file_path, format="audio/mp3")

                            # Download button
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    label=f"Download {file_name}",
                                    data=f.read(),
                                    file_name=file_name,
                                )

            except Exception as e:
                st.error(f"Error while fetching files: {e}")

        elif option == "Contact Us":
            st.header("Contact Us")
            st.image("logo.png", width=300)
            st.markdown("""
                <h1 style='text-align: center; font-size: 36px;'>sparshdrishti@gmail.com</h1>
                <h2 style='text-align: center; font-size: 28px;'>Phone: +91 7827191427</h2>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
