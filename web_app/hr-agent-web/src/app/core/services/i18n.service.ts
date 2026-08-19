import { Injectable, signal, effect } from '@angular/core';
import { translations, Lang, TranslationKey } from './translations';

const LANG_STORAGE_KEY = 'app-lang';

@Injectable({ providedIn: 'root' })
export class I18nService {
  readonly lang = signal<Lang>(this.getInitialLang());

  constructor() {
    effect(() => {
      const currentLang = this.lang();
      document.documentElement.lang = currentLang;
      document.documentElement.dir = currentLang === 'ar' ? 'rtl' : 'ltr';
      localStorage.setItem(LANG_STORAGE_KEY, currentLang);
    });
  }

  t(key: TranslationKey, params?: Record<string, string | number>): string {
    let text: string = translations[this.lang()][key] ?? key;

    if (params) {
      for (const [param, value] of Object.entries(params)) {
        text = text.replace(`{${param}}`, String(value));
      }
    }

    return text;
  }

  toggle(): void {
    this.lang.set(this.lang() === 'ar' ? 'en' : 'ar');
  }

  setLang(lang: Lang): void {
    this.lang.set(lang);
  }

  private getInitialLang(): Lang {
    const saved = localStorage.getItem(LANG_STORAGE_KEY) as Lang | null;
    if (saved === 'ar' || saved === 'en') {
      return saved;
    }
    return 'ar';
  }
}