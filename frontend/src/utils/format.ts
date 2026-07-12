export const formatDate = (dateStr: string | undefined | null): string => {
  if (!dateStr) return '---';
  try {
    return new Date(dateStr).toLocaleDateString('en-CA');
  } catch {
    return String(dateStr);
  }
};

export const formatDateTime = (dateStr: string | undefined | null): string => {
  if (!dateStr) return '---';
  try {
    const d = new Date(dateStr);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch {
    return String(dateStr);
  }
};
