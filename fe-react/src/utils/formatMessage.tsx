import React from "react";

/**
 * Formats bot messages with proper indentation, bold headers, and structure.
 * Also formats ISO dates to readable format.
 */
export function formatMessage(text: string): React.ReactNode {
  const lines = text.split("\n");
  const formatted: React.ReactNode[] = [];

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    
    // Skip empty lines
    if (!trimmed) {
      formatted.push(<br key={`br-${index}`} />);
      return;
    }

    // Detect headers (lines ending with colon, usually labels)
    const headerMatch = trimmed.match(/^([^:]+):\s*(.*)$/);
    if (headerMatch) {
      const [, label, value] = headerMatch;
      
      // Check if it's a section header (all caps or specific patterns)
      if (label.length > 0 && label.length < 30 && !value) {
        formatted.push(
          <div key={index} style={{ marginTop: "0.75rem", marginBottom: "0.5rem" }}>
            <strong style={{ fontSize: "1.1em", color: "#1e40af" }}>{label}</strong>
          </div>
        );
      } else {
        // Key-value pair
        formatted.push(
          <div key={index} style={{ marginBottom: "0.5rem", paddingLeft: "0.5rem" }}>
            <strong style={{ color: "#1e40af" }}>{label}:</strong>{" "}
            {value ? formatValue(value) : null}
          </div>
        );
      }
      return;
    }

    // Detect list items (starting with dash, bullet, or number)
    const listMatch = trimmed.match(/^[-•*]\s+(.+)$/);
    if (listMatch) {
      // Format the list item content (which may contain dates)
      // Process the content to format dates first
      const listContentText = listMatch[1];
      const listContent = formatValue(listContentText);
      formatted.push(
        <div key={index} style={{ marginBottom: "0.4rem", paddingLeft: "1.5rem", textIndent: "-1rem" }}>
          • {listContent}
        </div>
      );
      return;
    }

    // Detect numbered lists
    const numberedMatch = trimmed.match(/^\d+[.)]\s+(.+)$/);
    if (numberedMatch) {
      formatted.push(
        <div key={index} style={{ marginBottom: "0.4rem", paddingLeft: "1.5rem" }}>
          {formatValue(trimmed)}
        </div>
      );
      return;
    }

    // Detect indented lines (preserve indentation)
    const indentMatch = line.match(/^(\s+)(.+)$/);
    if (indentMatch) {
      const indent = indentMatch[1].length;
      formatted.push(
        <div key={index} style={{ marginBottom: "0.4rem", paddingLeft: `${indent * 0.5}rem` }}>
          {formatValue(indentMatch[2])}
        </div>
      );
      return;
    }

    // Regular line
    formatted.push(
      <div key={index} style={{ marginBottom: "0.5rem" }}>
        {formatValue(trimmed)}
      </div>
    );
  });

  return <div>{formatted}</div>;
}

/**
 * Formats a date string from ISO format to readable format
 */
function formatDate(dateString: string): string {
  try {
    // Handle ISO format dates (with or without time)
    // JavaScript Date doesn't handle microseconds well, so truncate to milliseconds
    let cleanedDateString = dateString.trim();
    
    // If there are microseconds (more than 3 digits after the dot), truncate to milliseconds
    const microsecondMatch = cleanedDateString.match(/\.(\d+)$/);
    if (microsecondMatch && microsecondMatch[1].length > 3) {
      // Truncate to 3 digits (milliseconds)
      cleanedDateString = cleanedDateString.substring(0, cleanedDateString.length - (microsecondMatch[1].length - 3));
    }
    
    const date = new Date(cleanedDateString);
    if (isNaN(date.getTime())) {
      // Try parsing as ISO string directly
      const isoDate = new Date(cleanedDateString.replace('T', ' '));
      if (!isNaN(isoDate.getTime())) {
        const options: Intl.DateTimeFormatOptions = {
          year: "numeric",
          month: "long",
          day: "numeric",
          hour: "numeric",
          minute: "2-digit",
          hour12: true,
        };
        return isoDate.toLocaleString("en-US", options);
      }
      return dateString; // Return original if not a valid date
    }

    // Format: "December 13, 2025 at 12:20 PM"
    const options: Intl.DateTimeFormatOptions = {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    };

    return date.toLocaleString("en-US", options);
  } catch (e) {
    return dateString; // Return original if formatting fails
  }
}

/**
 * Formats a value, making certain patterns bold and formatting dates
 */
function formatValue(value: string): React.ReactNode {
  if (!value) return <>{value}</>;
  
  // First, replace ISO date formats with formatted dates
  let processedValue = value;
  
  // Pattern to match ISO dates: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS.microseconds
  // Also handles cases with spaces like "T12: 20:20" (flexible pattern)
  // Matches: 2025-12-13T12:20:20 or 2025-12-13T12: 20:20.322518 or 2025-12-13T12:20:20.322518
  // Pattern handles spaces anywhere in the time portion
  // More permissive: allows 1-2 digits for hours, minutes, seconds
  const isoDatePattern = /\d{4}-\d{2}-\d{2}T\d{1,2}\s*:\s*\d{1,2}\s*:\s*\d{1,2}(\.\d+)?/g;
  const dateMatches: Array<{ index: number; length: number; text: string }> = [];
  
  // Reset regex lastIndex and find all date matches
  isoDatePattern.lastIndex = 0;
  let dateMatch;
  while ((dateMatch = isoDatePattern.exec(processedValue)) !== null) {
    dateMatches.push({
      index: dateMatch.index,
      length: dateMatch[0].length,
      text: dateMatch[0],
    });
  }
  
  // Replace dates in reverse order to maintain indices
  if (dateMatches.length > 0) {
    dateMatches.reverse().forEach((dateMatchItem) => {
      // Clean up the date string (remove all spaces) before formatting
      const cleanedDate = dateMatchItem.text.replace(/\s+/g, '');
      const formattedDate = formatDate(cleanedDate);
      // Replace the date in the processed value
      processedValue =
        processedValue.substring(0, dateMatchItem.index) +
        formattedDate +
        processedValue.substring(dateMatchItem.index + dateMatchItem.length);
    });
  }
  
  // Split by common separators and format
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;

  // Pattern to detect key-value-like structures within the value
  const patterns = [
    // Currency amounts
    /\$[\d,]+\.?\d*/g,
    // Numbers that might be IDs (2+ digits)
    /\b\d{2,}\b/g,
  ];

  // Find all pattern matches (for highlighting)
  const patternMatches: Array<{ start: number; end: number; text: string }> = [];
  patterns.forEach((pattern) => {
    const regex = new RegExp(pattern.source, pattern.flags);
    let match;
    while ((match = regex.exec(processedValue)) !== null) {
      patternMatches.push({
        start: match.index,
        end: match.index + match[0].length,
        text: match[0],
      });
    }
  });

  // Sort pattern matches by start position and remove overlaps
  patternMatches.sort((a, b) => a.start - b.start);
  const filteredMatches: Array<{ start: number; end: number; text: string }> = [];
  patternMatches.forEach((match) => {
    if (filteredMatches.length === 0 || match.start >= filteredMatches[filteredMatches.length - 1].end) {
      filteredMatches.push(match);
    }
  });

  // Build formatted parts
  if (filteredMatches.length > 0) {
    filteredMatches.forEach((match, idx) => {
      if (match.start > lastIndex) {
        parts.push(processedValue.substring(lastIndex, match.start));
      }
      parts.push(
        <strong key={`match-${idx}`} style={{ color: "#059669" }}>
          {match.text}
        </strong>
      );
      lastIndex = match.end;
    });

    if (lastIndex < processedValue.length) {
      parts.push(processedValue.substring(lastIndex));
    }
    return <>{parts}</>;
  } else {
    // No pattern matches, but dates may have been replaced
    // Return the processed value (which has dates formatted) as a string wrapped in React node
    return <>{processedValue}</>;
  }
}

