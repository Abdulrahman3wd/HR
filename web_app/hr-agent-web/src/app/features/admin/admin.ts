import { Component, inject, signal, OnInit } from '@angular/core';
import { ReactiveFormsModule, FormsModule, FormBuilder, Validators } from '@angular/forms';
import { LucideAngularModule, Users, FileText, Building2, Pencil, Trash2, Upload, Clock, Settings, CalendarHeart } from 'lucide-angular';
import { TranslationKey } from '../../core/services/translations';
import { AdminService } from '../../core/services/admin.service';
import { DepartmentService } from '../../core/services/department.service';
import { CompanySettingsService } from '../../core/services/company-settings.service';
import { I18nService } from '../../core/services/i18n.service';
import { AdminUserRecord, UserRole } from '../../core/models/admin.model';
import { Department } from '../../core/models/department.model';
import { CompanySettings, PublicHoliday } from '../../core/models/company-settings.model';
import { ToastService } from '../../core/services/toast.service';
import { ConfirmDialogService } from '../../core/services/confirm-dialog.service';
type AdminTab = 'users' | 'departments' | 'docs' | 'attendance' | 'settings';

@Component({
  selector: 'app-admin',
  imports: [ReactiveFormsModule, FormsModule, LucideAngularModule],
  templateUrl: './admin.html',
  styleUrl: './admin.css',
})
export class Admin implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly adminService = inject(AdminService);
  private readonly departmentService = inject(DepartmentService);
  private readonly companySettingsService = inject(CompanySettingsService);
  protected readonly i18n = inject(I18nService);
  private readonly toast = inject(ToastService);
  private readonly confirmDialog = inject(ConfirmDialogService);
  protected readonly UsersIcon = Users;
  protected readonly DocsIcon = FileText;
  protected readonly DeptIcon = Building2;
  protected readonly EditIcon = Pencil;
  protected readonly DeleteIcon = Trash2;
  protected readonly UploadIcon = Upload;
  protected readonly AttendanceIcon = Clock;
  protected readonly SettingsIcon = Settings;
  protected readonly HolidayIcon = CalendarHeart;

  protected readonly weekDays = [0, 1, 2, 3, 4, 5, 6];

  protected readonly activeTab = signal<AdminTab>('users');

  // ---------- Users state ----------
  protected readonly users = signal<AdminUserRecord[]>([]);
  protected readonly editingId = signal<string | null>(null);
  protected readonly userStatus = signal<{ type: 'success' | 'error'; text: string } | null>(null);
  protected readonly isSavingUser = signal(false);

  protected readonly userForm = this.fb.nonNullable.group({
    employee_id: ['', Validators.required],
    full_name: ['', Validators.required],
    department_id: [null as number | null],
    manager_id: [null as string | null],
    password: [''],
    role: ['employee' as UserRole, Validators.required],
    annual_leave_balance: [21, Validators.required],
    sick_leave_balance: [7, Validators.required],
  });

  // ---------- Departments state ----------
  protected readonly departments = signal<Department[]>([]);
  protected readonly newDeptName = signal('');
  protected readonly deptStatus = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  // ---------- Docs state ----------
  protected readonly docs = signal<string[]>([]);
  protected readonly selectedFile = signal<File | null>(null);
  protected readonly isUploading = signal(false);
  protected readonly docStatus = signal<{ type: 'success' | 'error'; text: string } | null>(null);
  // ---------- Attendance import state ----------
  protected readonly attendanceFile = signal<File | null>(null);
  protected readonly isImportingAttendance = signal(false);
  protected readonly attendanceImportStatus = signal<{ type: 'success' | 'error'; text: string } | null>(null);

    // ---------- Company settings state ----------
  protected readonly settings = signal<CompanySettings | null>(null);
  protected readonly selectedWeekendDays = signal<Set<number>>(new Set());
  protected readonly settingsForm = this.fb.nonNullable.group({
    work_start_time: ['09:00'],
    work_end_time: ['17:00'],
    flex_minutes: [60],
    monthly_late_allowance_minutes: [120],
  });
  protected readonly isSavingSettings = signal(false);
  protected readonly settingsStatus = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  // ---------- Holidays state ----------
  protected readonly holidays = signal<PublicHoliday[]>([]);
  protected readonly newHolidayDate = signal('');
  protected readonly newHolidayName = signal('');
  
  ngOnInit(): void {
    this.loadUsers();
    this.loadDepartments();
    this.loadDocs();
    this.loadSettings();
    this.loadHolidays();
  }
  protected switchTab(tab: AdminTab): void {
    this.activeTab.set(tab);
  }

  // ---------- Users logic ----------
  private loadUsers(): void {
    this.adminService.listUsers().subscribe({
      next: (data) => this.users.set(data.users),
    });
  }

  protected departmentName(departmentId: number | null): string {
    if (!departmentId) return '—';
    return this.departments().find((d) => d.id === departmentId)?.name ?? '—';
  }

  protected startEdit(user: AdminUserRecord): void {
    this.editingId.set(user.employee_id);
    this.userForm.patchValue({
      employee_id: user.employee_id,
      full_name: user.full_name,
      department_id: user.department_id,
      manager_id: user.manager_id,
      password: '',
      role: user.role,
      annual_leave_balance: user.annual_leave_balance,
      sick_leave_balance: user.sick_leave_balance,
    });
    this.userForm.controls.employee_id.disable();
  }

  protected cancelEdit(): void {
    this.editingId.set(null);
    this.userForm.reset({
      employee_id: '',
      full_name: '',
      department_id: null,
      manager_id: null,
      password: '',
      role: 'employee',
      annual_leave_balance: 21,
      sick_leave_balance: 7,
    });
    this.userForm.controls.employee_id.enable();
  }

  protected onUserFormSubmit(): void {
    if (this.userForm.invalid) {
      this.userForm.markAllAsTouched();
      return;
    }

    this.isSavingUser.set(true);
    this.userStatus.set(null);
    const raw = this.userForm.getRawValue();
    const editingId = this.editingId();

    if (editingId) {
      const updates = {
        full_name: raw.full_name,
        department_id: raw.department_id,
        manager_id: raw.manager_id,
        role: raw.role,
        annual_leave_balance: raw.annual_leave_balance,
        sick_leave_balance: raw.sick_leave_balance,
        ...(raw.password ? { password: raw.password } : {}),
      };

      this.adminService.updateUser(editingId, updates).subscribe({
        next: () => {
          this.isSavingUser.set(false);
          this.cancelEdit();
          this.loadUsers();
          this.toast.success('User updated successfully');
        },
        error: (err) => {
          this.isSavingUser.set(false);
          this.userStatus.set({ type: 'error', text: err.error?.detail || 'Error' });
          this.toast.error('Failed to update user');
        },
      });
    } else {
      this.adminService.createUser(raw).subscribe({
        next: () => {
          this.isSavingUser.set(false);
          this.cancelEdit();
          this.loadUsers();
          this.toast.success('User created successfully');
        },
        error: (err) => {
          this.isSavingUser.set(false);
          this.userStatus.set({ type: 'error', text: err.error?.detail || 'Error' });
          this.toast.error('Failed to create user');
        },
      });
    }
  }

  protected async deleteUser(employeeId: string): Promise<void> {
    const confirmed = await this.confirmDialog.confirm('Do you really want to delete this user? This action cannot be undone.');
    if (!confirmed) return;

    this.adminService.deleteUser(employeeId).subscribe({
      next: () => {
        this.loadUsers();
        this.toast.success('User deleted successfully');
      },
      error: (err) => this.toast.error(err.error?.detail || 'Error deleting user'),
    });
  }

  protected roleLabel(role: UserRole): string {
    if (role === 'admin') return this.i18n.t('account_role_admin');
    if (role === 'hr') return this.i18n.t('account_role_hr');
    return this.i18n.t('account_role_employee');
  }

  // ---------- Departments logic ----------
  private loadDepartments(): void {
    this.departmentService.list().subscribe({
      next: (data) => this.departments.set(data.departments),
    });
  }

  protected addDepartment(): void {
    const name = this.newDeptName().trim();
    if (!name) return;

    this.departmentService.create({ name }).subscribe({
      next: () => {
        this.newDeptName.set('');
        this.loadDepartments();
        this.toast.success('Department added successfully');
      },
      error: (err) => {
        this.deptStatus.set({ type: 'error', text: err.error?.detail || 'Error' });
        this.toast.error('Failed to add department');
      },
    });
  }

  protected async deleteDepartment(id: number): Promise<void> {
    const confirmed = await this.confirmDialog.confirm('Do you really want to delete this department? This action cannot be undone.');
    if (!confirmed) return;

    this.departmentService.delete(id).subscribe({
      next: () => {
        this.loadDepartments();
        this.toast.success('Department deleted successfully');
      },
      error: (err) => this.toast.error(err.error?.detail || 'Error deleting department'),
    });
  }
  // ---------- Docs logic ----------
  private loadDocs(): void {
    this.adminService.listDocs().subscribe({
      next: (data) => this.docs.set(data.files),
    });
  }

  protected onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile.set(input.files?.[0] ?? null);
  }

  protected uploadFile(): void {
    const file = this.selectedFile();
    if (!file) {
      this.docStatus.set({ type: 'error', text: this.i18n.t('admin_no_file_selected') });
      return;
    }

    this.isUploading.set(true);
    this.docStatus.set(null);

    this.adminService.uploadDoc(file).subscribe({
      next: () => {
        this.isUploading.set(false);
        this.docStatus.set({ type: 'success', text: this.i18n.t('admin_upload_success') });
        this.selectedFile.set(null);
        this.loadDocs();
        this.toast.success('Document uploaded successfully');
      },
      error: () => {
        this.isUploading.set(false);
        this.docStatus.set({ type: 'error', text: this.i18n.t('admin_upload_error') });
        this.toast.error('Failed to upload document');
      },
    });
  }

  protected async deleteDoc(filename: string): Promise<void> {
    const confirmed = await this.confirmDialog.confirm('Do you really want to delete this document? This action cannot be undone.');
    if (!confirmed) return;

    this.adminService.deleteDoc(filename).subscribe({
      next: () => {
        this.loadDocs();
        this.toast.success('Document deleted successfully');
      },
      error: (err) => this.toast.error(err.error?.detail || 'Error deleting document'),
    });
  }
    // ---------- Attendance import logic ----------
  protected onAttendanceFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.attendanceFile.set(input.files?.[0] ?? null);
  }

  protected importAttendance(): void {
    const file = this.attendanceFile();
    if (!file) {
      this.attendanceImportStatus.set({ type: 'error', text: this.i18n.t('admin_no_file_selected') });
      return;
    }

    this.isImportingAttendance.set(true);
    this.attendanceImportStatus.set(null);

    this.adminService.importAttendance(file).subscribe({
      next: (result) => {
        this.isImportingAttendance.set(false);
        const importedMsg = this.i18n.t('admin_attendance_imported', { count: result.imported_rows });
        const skippedMsg = result.skipped_rows > 0
          ? ` — ${this.i18n.t('admin_attendance_skipped', { count: result.skipped_rows })}`
          : '';
        this.attendanceImportStatus.set({ type: 'success', text: importedMsg + skippedMsg });
        this.attendanceFile.set(null);
      },
      error: (err) => {
        this.isImportingAttendance.set(false);
        this.attendanceImportStatus.set({ type: 'error', text: err.error?.detail || 'Error' });
      },
    });
  }

    // ---------- Company settings logic ----------
  private loadSettings(): void {
    this.companySettingsService.getSettings().subscribe({
      next: (data) => {
        this.settings.set(data);
        this.selectedWeekendDays.set(new Set(data.weekend_days));
        this.settingsForm.patchValue({
          work_start_time: data.work_start_time,
          work_end_time: data.work_end_time,
          flex_minutes: data.flex_minutes,
          monthly_late_allowance_minutes: data.monthly_late_allowance_minutes,
        });
      },
    });
  }

  protected toggleWeekendDay(day: number): void {
    const current = new Set(this.selectedWeekendDays());
    if (current.has(day)) {
      current.delete(day);
    } else {
      current.add(day);
    }
    this.selectedWeekendDays.set(current);

  }

  protected saveSettings(): void {
    this.isSavingSettings.set(true);
    this.settingsStatus.set(null);
    const raw = this.settingsForm.getRawValue();

    this.companySettingsService
      .updateSettings({
        ...raw,
        weekend_days: Array.from(this.selectedWeekendDays()),
      })
      .subscribe({
        next: (data) => {
          this.isSavingSettings.set(false);
          this.settings.set(data);
          this.settingsStatus.set({ type: 'success', text: this.i18n.t('settings_saved') });
          this.toast.success('Settings saved successfully');
        },
        error: (err) => {
          this.isSavingSettings.set(false);
          this.settingsStatus.set({ type: 'error', text: err.error?.detail || 'Error' });
          this.toast.error('Failed to save settings');
        },
      });
  }

  // ---------- Holidays logic ----------
  private loadHolidays(): void {
    this.companySettingsService.listHolidays().subscribe({
      next: (data) => this.holidays.set(data.holidays),
    });
  }

  protected addHoliday(): void {
    const date = this.newHolidayDate();
    const name = this.newHolidayName().trim();
    if (!date || !name) return;

    this.companySettingsService.addHoliday({ date, name }).subscribe({
      next: () => {
        this.newHolidayDate.set('');
        this.newHolidayName.set('');
        this.loadHolidays();
        this.toast.success('Holiday added successfully');
      },
    });
  }

  protected deleteHoliday(id: number): void {
    this.companySettingsService.deleteHoliday(id).subscribe({
      next: () => {
        this.loadHolidays();
        this.toast.success('Holiday deleted successfully');
      },
      error: (err) => {
        this.toast.error(err.error?.detail || 'Error deleting holiday');
      }
    });
  }
    protected dayLabel(day: number): string {
    return this.i18n.t(('day_' + day) as TranslationKey);
  }
}