# PDC access and enrollment workflow

## Roles and permissions

- **Administrator:** a Django staff member or superuser (`is_staff` or `is_superuser`). Only administrators manage student/teacher records, courses, PDC events, enrollment approvals, reports, certificates, and all attendance.
- **Student:** accounts are created through `/register/` using a student ID that the PDC office has already entered. Registration links that account to the existing student record and assigns only the `Student` group; it never grants staff access. Students can browse courses that have not ended, submit one enrollment request per course, and see pending/approved/rejected status.
- **Teacher:** teacher accounts are created and assigned by an administrator. The teacher account must be non-staff, belong to the `Teacher` group, and be linked to the teacher profile. Teachers can see only assigned courses and take attendance only for approved enrollees in those courses. They cannot manage institutional records.

## Student enrollment procedure

1. An administrator adds the student's official record from **Students → Register Student**. Give the student the exact student ID entered in that record.
2. The student opens `/register/`, creates a username and password, and enters that student ID. A student ID can be linked to only one account.
3. After sign-in, the student portal lists eligible courses. **Request enrollment** creates a pending request; it does not immediately grant course access.
4. An administrator reviews requests under **Enrollments** and approves or rejects them. The student sees the decision in their portal.
5. A teacher must have a non-staff account, membership in the `Teacher` group, and a linked teacher profile. The administrator assigns courses to that profile.

## Local update

The account/profile links and enrollment status require migration `0009_student_teacher_accounts_and_enrollment_status.py`. Back up `db.sqlite3` before updating, then run `python manage.py migrate` and `python manage.py check`.
