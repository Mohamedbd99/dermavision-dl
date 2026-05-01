import api from "./api";

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
}

export async function register(data: RegisterPayload): Promise<User> {
  const res = await api.post<User>("/auth/register", data);
  return res.data;
}

export async function login(data: LoginPayload): Promise<string> {
  const form = new URLSearchParams();
  form.append("username", data.username);
  form.append("password", data.password);

  const res = await api.post<{ access_token: string; token_type: string }>(
    "/auth/login",
    form,
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
  );
  const token = res.data.access_token;
  localStorage.setItem("token", token);
  return token;
}

export async function getMe(): Promise<User> {
  const res = await api.get<User>("/me");
  return res.data;
}

export function logout(): void {
  localStorage.removeItem("token");
}
