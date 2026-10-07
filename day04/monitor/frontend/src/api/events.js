import { request } from "./client";

export async function fetchEvents(eventType) {
  let url = "/api/events";
  if (eventType) {
    const params = new URLSearchParams({ event_type: eventType });
    url += `?${params.toString()}`;
  }
  const data = await request(url);
  return data.events || [];
}
