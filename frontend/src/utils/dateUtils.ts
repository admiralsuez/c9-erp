/**
 * Date utilities for report date range presets
 */

export interface DateRange {
  from: Date;
  to: Date;
}

/**
 * Get today's date range (00:00 to 23:59)
 */
export const getTodayRange = (): DateRange => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const end = new Date(today);
  end.setHours(23, 59, 59, 999);
  return { from: today, to: end };
};

/**
 * Get this week's date range (Monday to Sunday)
 */
export const getThisWeekRange = (): DateRange => {
  const today = new Date();
  const dayOfWeek = today.getDay();
  const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
  
  const monday = new Date(today);
  monday.setDate(today.getDate() - daysToMonday);
  monday.setHours(0, 0, 0, 0);
  
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  sunday.setHours(23, 59, 59, 999);
  
  return { from: monday, to: sunday };
};

/**
 * Get this month's date range
 */
export const getThisMonthRange = (): DateRange => {
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
  firstDay.setHours(0, 0, 0, 0);
  
  const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
  lastDay.setHours(23, 59, 59, 999);
  
  return { from: firstDay, to: lastDay };
};

/**
 * Get this quarter's date range
 */
export const getThisQuarterRange = (): DateRange => {
  const today = new Date();
  const quarter = Math.floor(today.getMonth() / 3);
  
  const firstDay = new Date(today.getFullYear(), quarter * 3, 1);
  firstDay.setHours(0, 0, 0, 0);
  
  const lastDay = new Date(today.getFullYear(), (quarter + 1) * 3, 0);
  lastDay.setHours(23, 59, 59, 999);
  
  return { from: firstDay, to: lastDay };
};

/**
 * Get this year's date range
 */
export const getThisYearRange = (): DateRange => {
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), 0, 1);
  firstDay.setHours(0, 0, 0, 0);
  
  const lastDay = new Date(today.getFullYear(), 11, 31);
  lastDay.setHours(23, 59, 59, 999);
  
  return { from: firstDay, to: lastDay };
};

/**
 * Get last 7 days date range
 */
export const getLast7DaysRange = (): DateRange => {
  const to = new Date();
  to.setHours(23, 59, 59, 999);
  
  const from = new Date(to);
  from.setDate(to.getDate() - 6);
  from.setHours(0, 0, 0, 0);
  
  return { from, to };
};

/**
 * Get last 30 days date range
 */
export const getLast30DaysRange = (): DateRange => {
  const to = new Date();
  to.setHours(23, 59, 59, 999);
  
  const from = new Date(to);
  from.setDate(to.getDate() - 29);
  from.setHours(0, 0, 0, 0);
  
  return { from, to };
};

/**
 * Format date to ISO string (YYYY-MM-DD)
 */
export const formatDateISO = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * Format date for display (e.g., "Jan 1, 2026")
 */
export const formatDateDisplay = (date: Date): string => {
  const options: Intl.DateTimeFormatOptions = { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  };
  return date.toLocaleDateString('en-US', options);
};

/**
 * Parse ISO date string to Date object
 */
export const parseISO = (dateString: string): Date => {
  return new Date(dateString + 'T00:00:00Z');
};

/**
 * Date preset definitions for UI
 */
export const datePresets = [
  {
    label: 'Today',
    getValue: getTodayRange,
  },
  {
    label: 'This Week',
    getValue: getThisWeekRange,
  },
  {
    label: 'This Month',
    getValue: getThisMonthRange,
  },
  {
    label: 'This Quarter',
    getValue: getThisQuarterRange,
  },
  {
    label: 'This Year',
    getValue: getThisYearRange,
  },
  {
    label: 'Last 7 Days',
    getValue: getLast7DaysRange,
  },
  {
    label: 'Last 30 Days',
    getValue: getLast30DaysRange,
  },
];
