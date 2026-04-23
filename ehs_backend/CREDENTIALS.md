# EHS Portal — Test Credentials

## Admin
| Student ID | Password | Role |
|------------|----------|------|
| ADMIN001 | Admin@123 | admin |

## Students (all use password: `Test@1234`)

| Student ID | Full Name | Email |
|------------|-----------|-------|
| contin | Aisha Rahman | stu001@ehs.test |
| STU002 | Ben Lim | stu002@ehs.test |
| STU003 | Caleb Tan | stu003@ehs.test |
| STU004 | Diana Ng | stu004@ehs.test |
| STU005 | Ethan Koh | stu005@ehs.test |
| STU006 | Fiona Teo | stu006@ehs.test |
| STU007 | Gabriel Lee | stu007@ehs.test |
| STU008 | Hannah Wong | stu008@ehs.test |
| STU009 | Isaac Chen | stu009@ehs.test |
| STU010 | Jaya Patel | stu010@ehs.test |
| STU011 | Kevin Ong | stu011@ehs.test |
| STU012 | Linh Tran | stu012@ehs.test |
| STU013 | Marcus Ho | stu013@ehs.test |
| STU014 | Nadia Singh | stu014@ehs.test |
| STU015 | Owen Chua | stu015@ehs.test |
| STU016 | Priya Sharma | stu016@ehs.test |
| STU017 | Quincy Yap | stu017@ehs.test |
| STU018 | Rachel Lim | stu018@ehs.test |
| STU019 | Samuel Goh | stu019@ehs.test |
| STU020 | Tanya Kumar | stu020@ehs.test |
| STU021 | Uma Nair | stu021@ehs.test |
| STU022 | Vikram Singh | stu022@ehs.test |
| STU023 | Wei Xin Tan | stu023@ehs.test |

## How to Login

### Streamlit UI
1. Run: `streamlit run ehs_frontend.py`
2. Enter Student ID and password in the sidebar

### Swagger UI
1. Open: http://localhost:8000/docs
2. Use `POST /api/v1/auth/login` with `{"student_id": "STU001", "password": "Test@1234"}`
3. Copy `access_token` and click **Authorize** (top right)
