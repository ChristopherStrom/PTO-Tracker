# User Password Update Utility

This utility allows you to update the password for a specified user in the PTO Tracker application. 

## Usage

From the root directory of your project, you can run the utility using the following command:

\`\`\`sh
python3 ./utils/update_user_pass.py <username> <new_password>
\`\`\`

Replace `<username>` with the username of the user you want to update and `<new_password>` with the new password you want to set.

## Example

To update the password for the user `Chris.Strom` to `new_password123`, you would run:

\`\`\`sh
python3 ./utils/update_user_pass.py Chris.Strom new_password123
\`\`\`

## File Structure

- `utils/update_user_pass.py`: The main script to update the user password.

## Notes

- Ensure that the Flask application and database are correctly set up and configured.
- This script directly modifies the user's password in the database, so use it with caution.
- The new password is hashed before being stored in the database.

## Requirements

- Python 3
- Flask
- SQLAlchemy
- Werkzeug

## Installation

Make sure you have the required dependencies installed. You can install them using:

\`\`\`sh
pip install Flask SQLAlchemy Werkzeug
\`\`\`

## License

This utility is free for non-commercial use. For commercial use, a paid license is required. Please contact `cstrom@clsio.com` for more information. All modifications must also comply with this license.

## Author

This utility was created by Chris Strom.
