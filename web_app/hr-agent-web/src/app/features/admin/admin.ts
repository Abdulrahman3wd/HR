import { Component, inject, signal, OnInit } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { LucideAngularModule, Users, FileText, Pencil, Trash2, Upload, X } from 'lucide-angular';

import { AdminService } from '../../core/services/admin.service';
import { I18nService } from '../../core/services/i18n.service';
import { AdminUserRecord, UserRole } from '../../core/models/admin.model';

type AdminTab = 'users' | 'docs';

@Component({
  selector: 'app-admin',
  imports: [ReactiveFormsModule, LucideAngularModule],
  templateUrl: './admin.html',
  styleUrl: './admin.css',
})
export class Admin implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly adminService = inject(AdminService);
  protected readonly i18n = inject(I18nService);

  protected readonly UsersIcon = Users;
  protected readonly DocsIcon = FileText;
  protected readonly EditIcon = Pencil;
  protected readonly DeleteIcon = Trash2;
  protected readonly UploadIcon = Upload;
  protected readonly CloseIcon = X;

  protected readonly activeTab = signal<AdminTab>('users');

  // ---------- Users state ----------
  protected readonly users = signal<AdminUserRecord[]>([]);
  protected readonly editingId = signal<string | null>(null);
  protected readonly userStatus = signal<{ type: 'success' | 'error'; text: string } | null>(null);
  protected readonly isSavingUser = signal(false);

  protected readonly userForm = this.fb.nonNullable.group({
    employee_id: ['', Validators.required],
    full_name: ['', Validators.required],
    department: ['', Validators.required],
    password: [''],
    role: ['employee' as UserRole, Validators.required],
    annual_leave_balance: [21, Validators.required],
    sick_leave_balance: [7, Validators.required],
  });

  // ---------- Docs state ----------
  protected readonly docs = signal<string[]>([]);
  protected readonly selectedFile = signal<File | null>(null);
  protected readonly isUploading = signal(false);
  protected readonly docStatus = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  ngOnInit(): void {
    this.loadUsers();
    this.loadDocs();
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

  protected startEdit(user: AdminUserRecord): void {
    this.editingId.set(user.employee_id);
    this.userForm.patchValue({
      employee_id: user.employee_id,
      full_name: user.full_name,
      department: user.department,
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
      department: '',
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
        department: raw.department,
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
        },
        error: (err) => {
          this.isSavingUser.set(false);
          this.userStatus.set({ type: 'error', text: err.error?.detail || 'Error' });
        },
      });
    } else {
      this.adminService.createUser(raw).subscribe({
        next: () => {
          this.isSavingUser.set(false);
          this.cancelEdit();
          this.loadUsers();
        },
        error: (err) => {
          this.isSavingUser.set(false);
          this.userStatus.set({ type: 'error', text: err.error?.detail || 'Error' });
        },
      });
    }
  }

  protected deleteUser(employeeId: string): void {
    if (!confirm(this.i18n.t('admin_confirm_delete_user'))) return;

    this.adminService.deleteUser(employeeId).subscribe({
      next: () => this.loadUsers(),
    });
  }

  protected roleLabel(role: UserRole): string {
    return role === 'admin' ? this.i18n.t('account_role_admin') : this.i18n.t('account_role_employee');
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
      },
      error: () => {
        this.isUploading.set(false);
        this.docStatus.set({ type: 'error', text: this.i18n.t('admin_upload_error') });
      },
    });
  }

  protected deleteDoc(filename: string): void {
    if (!confirm(this.i18n.t('admin_confirm_delete_doc'))) return;

    this.adminService.deleteDoc(filename).subscribe({
      next: () => this.loadDocs(),
    });
  }
}