export interface NetSalary {
  employee_id: string;
  year: number;
  month: number;
  basic_salary: number;
  social_insurance_amount: number;
  health_insurance_amount: number;
  late_excess_minutes: number;
  late_deduction_amount: number;
  overtime_minutes: number;
  overtime_amount: number;
  total_deductions: number;
  net_salary: number;
}