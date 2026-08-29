import { GENERATE_SLUG_FROM_TITLE } from '../config'

export default function (title: string, staticSlug: string) {
  if (staticSlug) {
    const cleanStatic = staticSlug.replace(/\\/g, '/').split('/').pop()?.replace(/\.(md|json)$/, '');
    if (cleanStatic) return cleanStatic;
  }

  const generated = title
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\w-]/g, '')
    .replace(/^-+|-+$/g, '');

  return generated || staticSlug || 'post';
}
