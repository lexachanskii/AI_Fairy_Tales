import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function RegisterPage() {
  const nav = useNavigate()
  const [form, setForm]   = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (form.username.length < 3) return setError('Логин — минимум 3 символа')
    if (form.password.length < 5) return setError('Пароль — минимум 5 символов')
    setLoading(true)
    try {
      await api.register(form.username, form.password)
      nav('/login', { state: { registered: true } })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="card">
        <p className="brand">✦ AI Fairy Tales ✦</p>
        <h2>Создать аккаунт</h2>
        <p className="subtitle">Создайте аккаунт родителя, а затем заполните отдельный профиль ребёнка для персональных сказок</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Логин</label>
            <input
              type="text" value={form.username}
              onChange={set('username')}
              placeholder="от 3 символов" autoComplete="username"
            />
          </div>
          <div className="field">
            <label>Пароль</label>
            <input
              type="password" value={form.password}
              onChange={set('password')}
              placeholder="от 5 символов" autoComplete="new-password"
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? <><span className="spinner" /> Регистрируемся…</> : '✦ Зарегистрироваться'}
          </button>
        </form>

        <div className="orn">✦</div>
        <p className="link-center">
          Уже есть аккаунт?{' '}
          <Link to="/login">Войти</Link>
        </p>
      </div>
    </div>
  )
}
