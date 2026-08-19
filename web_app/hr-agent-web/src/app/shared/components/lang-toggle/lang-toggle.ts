import { Component, inject } from '@angular/core';
import { LucideAngularModule, Languages } from 'lucide-angular';
import { I18nService } from '../../../core/services/i18n.service';

@Component({
  selector: 'app-lang-toggle',
  imports: [LucideAngularModule],
  templateUrl: './lang-toggle.html',
  styleUrl: './lang-toggle.css',
})
export class LangToggle {
  protected readonly i18n = inject(I18nService);
  protected readonly LanguagesIcon = Languages;
}