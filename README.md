# Task Manager Application

This Task Manager application allows users to manage their tasks efficiently through a user-friendly interface. Users can register, log in, create, update, and delete tasks, as well as download their task lists as PDF documents for offline use.

## Features Implemented

1. **User Authentication and Authorization**
   - Users can register with a unique username and password.
   - Secure login/logout functionality using Flask-Login.
   - Authorization checks ensure only authenticated users can access certain routes.

2. **Task Management**
   - Create tasks with titles, descriptions, and due dates.
   - View, update, and delete tasks associated with the logged-in user.

3. **PDF Generation and Download**
   - Tasks can be downloaded as PDF documents.
   - PDFs include formatted task lists with checkboxes, titles, descriptions, and due dates.
   - Implemented using Flask, ReportLab for PDF generation, and Flask's Response for file download.

4. **Responsive Design**
   - HTML templates utilize Bootstrap for responsiveness.
   - Ensures optimal viewing and usability across various devices and screen sizes.

5. **Error Handling**
   - Custom error pages (404 and 500) provide a better user experience in case of errors.
   - Error messages and redirects are tailored to user actions for clarity and efficiency.

## Important Features

- **User Registration and Authentication:** Secure access to the task management system, ensuring only registered users can manage tasks.
  
- **Task Creation and Management:** Users can add, update, and delete tasks, facilitating effective organization and planning.

- **PDF Download:** Convenient export feature enables users to download their task lists as PDF documents for offline reference.

- **Responsive Design:** Ensures the application is accessible and usable on different devices, enhancing overall user experience.

## Deployment Information

- **Deployed Application:** [Task Manager on PythonAnywhere](https://jarkapeed2003.pythonanywhere.com/)
- **GitHub Repository:** [Task Manager GitHub Repository](https://github.com/deepakraaaj/TaskManger.git)

## Getting Started

To run the application locally:

1. Clone the repository from GitHub:
   ```
   git clone https://github.com/deepakraaaj/TaskManger.git
   cd TaskManger
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Access the application in your web browser at [http://localhost:5000](http://localhost:5000).

