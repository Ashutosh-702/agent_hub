/**
 * Date utility functions for formatting dates in IST (Indian Standard Time)
 */

const IST_TIMEZONE = 'Asia/Kolkata';

/**
 * Format a date string or Date object to IST locale string
 */
export function formatDateIST(date: string | Date | null | undefined): string {
  if (!date) return '—';
  
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return dateObj.toLocaleString('en-IN', {
      timeZone: IST_TIMEZONE,
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  } catch {
    return String(date);
  }
}

/**
 * Format a date string or Date object to IST date string (date only, no time)
 */
export function formatDateOnlyIST(date: string | Date | null | undefined): string {
  if (!date) return '—';
  
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return dateObj.toLocaleDateString('en-IN', {
      timeZone: IST_TIMEZONE,
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return String(date);
  }
}

/**
 * Format a date string or Date object to IST time string (time only)
 */
export function formatTimeIST(date: string | Date | null | undefined): string {
  if (!date) return '—';
  
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return dateObj.toLocaleTimeString('en-IN', {
      timeZone: IST_TIMEZONE,
      hour: 'numeric',
      minute: '2-digit',
    });
  } catch {
    return String(date);
  }
}

/**
 * Format a date string or Date object to IST locale string (short format for activity timeline)
 */
export function formatDateShortIST(date: string | Date | null | undefined): string {
  if (!date) return '—';
  
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return dateObj.toLocaleString('en-IN', {
      timeZone: IST_TIMEZONE,
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  } catch {
    return String(date);
  }
}

/**
 * Get current date/time in IST
 */
export function getCurrentIST(): Date {
  const now = new Date();
  // Convert to IST by getting the string representation and parsing it
  const istString = now.toLocaleString('en-IN', { timeZone: IST_TIMEZONE });
  return new Date(istString);
}

/**
 * Convert a UTC date string to IST datetime-local input format (YYYY-MM-DDTHH:mm)
 * This is used for datetime-local input fields which expect local timezone
 */
export function utcToISTLocalInput(date: string | Date | null | undefined): string {
  if (!date) return '';
  
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    
    // Get IST date components using Intl.DateTimeFormat for reliable parsing
    const formatter = new Intl.DateTimeFormat('en-IN', {
      timeZone: IST_TIMEZONE,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
    
    const parts = formatter.formatToParts(dateObj);
    const year = parts.find(p => p.type === 'year')?.value || '';
    const month = parts.find(p => p.type === 'month')?.value || '';
    const day = parts.find(p => p.type === 'day')?.value || '';
    const hour = parts.find(p => p.type === 'hour')?.value || '';
    const minute = parts.find(p => p.type === 'minute')?.value || '';
    
    if (year && month && day && hour && minute) {
      return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}T${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`;
    }
    
    // Fallback: use manual calculation
    // Get UTC time and add IST offset (5:30)
    const utcTime = dateObj.getTime();
    const istOffsetMs = 5.5 * 60 * 60 * 1000; // IST is UTC+5:30
    const istTime = new Date(utcTime + istOffsetMs);
    
    const yearFallback = istTime.getUTCFullYear();
    const monthFallback = String(istTime.getUTCMonth() + 1).padStart(2, '0');
    const dayFallback = String(istTime.getUTCDate()).padStart(2, '0');
    const hourFallback = String(istTime.getUTCHours()).padStart(2, '0');
    const minuteFallback = String(istTime.getUTCMinutes()).padStart(2, '0');
    
    return `${yearFallback}-${monthFallback}-${dayFallback}T${hourFallback}:${minuteFallback}`;
  } catch {
    return '';
  }
}

/**
 * Convert a datetime-local input value (IST) to UTC ISO string
 * This is used when saving datetime-local input values
 * The input is interpreted as IST time and converted to UTC
 */
export function istLocalInputToUTC(localInput: string): string {
  if (!localInput) return '';
  
  try {
    // datetime-local input is in format YYYY-MM-DDTHH:mm
    // We need to interpret this as IST and convert to UTC
    const [datePart, timePart] = localInput.split('T');
    if (!datePart || !timePart) return '';
    
    const [year, month, day] = datePart.split('-').map(Number);
    const [hour, minute] = timePart.split(':').map(Number);
    
    // Create a date string in the format that can be parsed as IST
    // We'll create an ISO string and then adjust for IST offset
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}T${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:00`;
    
    // Create a date object - this will be interpreted in the browser's local timezone
    // But we want to interpret it as IST, so we need to convert
    // IST is UTC+5:30, so we need to subtract 5:30 from the IST time to get UTC
    
    // Method: Create a date assuming the input is in UTC, then add IST offset to get the actual UTC time
    // If input is "2026-01-18T14:30" in IST, that's "2026-01-18T09:00" in UTC (subtract 5:30)
    const tempDate = new Date(dateStr + 'Z'); // Parse as UTC
    // IST offset is +5:30 = 5.5 hours = 19800000 ms
    const istOffsetMs = 5.5 * 60 * 60 * 1000;
    const utcTimestamp = tempDate.getTime() - istOffsetMs;
    
    return new Date(utcTimestamp).toISOString();
  } catch {
    return '';
  }
}
