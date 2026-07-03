export const LOGIN_FORM_ACTION = "/login";
export const LOGIN_FORM_METHOD = "post";
export const DEFAULT_LOGIN_REDIRECT = "/pulpit";

export function resolveLoginRedirect(requested: string | null | undefined): string {
  return requested && requested.startsWith("/") && !requested.startsWith("//") ? requested : DEFAULT_LOGIN_REDIRECT;
}
