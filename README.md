# PTO Tracker Application

## Overview

The PTO Tracker is a web application designed to help organizations manage employee paid time off (PTO), emergency hours, and vacation hours. The application allows administrators to add users, edit user details, manage time off requests, and keep track of the available and used hours for each user.

## Features

- **User Management**: Add, edit, and delete users.
- **Time Off Management**: Record and manage PTO, emergency, and vacation hours.
- **Bucket Changes**: Track changes in the available hours for each category.
- **User Roles**: Differentiate between admin and regular user functionalities.
- **Reporting**: View detailed reports of time off and bucket changes.
- **PDF Export**: Generate PDF reports of time off history and current PTO and bucket totals.

## Installation

### Prerequisites

- Python 3.10 or higher
- `pip` (Python package installer)
- `virtualenv` (Python virtual environment tool)
- SQLite (included with Python)
- WeasyPrint

### Steps

1. **Clone the repository**:
    ```sh
    git clone https://github.com/yourusername/pto-tracker.git
    cd pto-tracker
    ```

2. **Create a virtual environment**:
    ```sh
    python -m venv venv
    ```

3. **Activate the virtual environment**:
    - On Windows:
        ```sh
        venv\Scripts\activate
        ```
    - On Unix or MacOS:
        ```sh
        source venv/bin/activate
        ```

4. **Install the required packages**:
    ```sh
    pip install -r requirements.txt
    ```

5. **Install WeasyPrint**:
    ```sh
    sudo apt-get install -y weasyprint
    ```

6. **Set up the database**:
    ```sh
    flask db init
    flask db migrate -m "Initial migration."
    flask db upgrade
    ```

7. **Run the application**:
    ```sh
    flask run
    ```

## Usage

### Accessing the Dashboard

1. **Login**: Use the credentials provided by the administrator to log in to the application.
2. **Dashboard**: The dashboard provides an overview of all users and their respective PTO, emergency, and vacation hours.
![Dashboard](images/Dashboard.png)

### Managing Time Off

1. **Add Time Off**: To add time off for a user, navigate to the "Add Time Off" page.
![Add Time Off](images/add_time_off.png)

2. **View User Details**: Click on a user's name in the dashboard to view detailed information about their time off and bucket changes.
![User Time](images/user_time.png)

### Editing User Information

1. **Edit User**: Admins can edit user details by navigating to the "Edit User" page.
![Edit User](images/edit_user.png)

### Generating Reports

1. **Export to PDF**: Admins can generate a PDF report of a user's time off history and current PTO and bucket totals. This option is available next to the user selection dropdown on the user details page.

## Sample Data

Here is an example of how the data is displayed in the application.
![Sample Data](images/sample_data.png)

## Contributing

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
    ```sh
    git clone https://github.com/yourusername/pto-tracker.git
    cd pto-tracker
    ```
3. **Create a new branch**:
    ```sh
    git checkout -b feature-branch
    ```
4. **Make your changes** and **commit them**:
    ```sh
    git commit -m "Description of changes"
    ```
5. **Push to your branch**:
    ```sh
    git push origin feature-branch
    ```
6. **Create a Pull Request** on GitHub.

# PTO Tracker License

## Overview

This license governs the use of the PTO Tracker application. By using this software, you agree to abide by the terms and conditions set forth in this document.

## Non-Commercial Use

You are free to use, modify, and distribute the PTO Tracker application for non-commercial purposes, subject to the following conditions:

- **Attribution**: You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
- **Non-Commercial**: You may not use the material for commercial purposes. 
- **No Additional Restrictions**: You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

## Commercial Use

Commercial use of the PTO Tracker application, including modified versions, requires a paid license. To obtain a commercial license, please contact us at:

**Email**: cstrom@clsio.com

## Disclaimer

This software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.

## Contact

For questions or issues regarding this license, please contact:

**Email**: cstrom@clsio.com

By using this software, you acknowledge that you have read and understood this license and agree to be bound by its terms and conditions.

## Support

For any questions or issues, please contact the project maintainer at [cstrom@clsio.com].
