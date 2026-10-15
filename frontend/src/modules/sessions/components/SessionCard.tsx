import { defineComponent, type PropType } from 'vue'
import { MapPin, Calendar, Clock, HelpCircle, Copy, QrCode } from 'lucide-vue-next'
import QRCode from 'qrcode'
import StatusChip from '../../../core/components/statusChip/StatusChip'
import Button from '@/core/components/button/Button'

export interface Session {
  id: string
  title: string
  status: 'ongoing' | 'upcoming' | 'completed'
  location: string
  date: string
  time: string
  questionsCount: number
}

export default defineComponent({
  name: 'SessionCard',
  components: {
    StatusChip,
    MapPin,
    Calendar,
    Clock,
    HelpCircle,
  },
  props: {
    session: {
      type: Object as PropType<Session>,
      required: true,
    },
  },
  emits: ['open-session', 'start-session', 'ranking-session', 'share'],
  setup(props, { emit }) {
    const downloadQrSvg = async () => {
      const url = `${window.location.origin}/#/session/${props.session.id}/join`
      const svg = await QRCode.toString(url, {
        type: 'svg',
      })

      const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' })
      const objectUrl = URL.createObjectURL(blob)

      const a = document.createElement('a')
      a.href = objectUrl
      a.download = `session-${props.session.title}.svg`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(objectUrl)
    }

    return () => (
      <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all duration-200">
        {/* Header */}
        <div class="flex flex-col gap-4">
          <div class="flex items-start justify-between gap-3">
            <StatusChip status={props.session.status} />

            {/* Actions */}
            <div class="flex flex-wrap justify-end gap-2">
              {(props.session.status === 'ongoing' || props.session.status === 'upcoming') && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => emit('start-session', props.session.id)}
                >
                  Open Session
                </Button>
              )}

              {props.session.status === 'upcoming' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => emit('open-session', props.session.id)}
                >
                  Edit
                </Button>
              )}

              {props.session.status === 'completed' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => emit('ranking-session', props.session.id)}
                >
                  Ranking
                </Button>
              )}

              {props.session.status !== 'completed' && (
                <button
                  onClick={() => emit('share', props.session.id)}
                  class="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition"
                >
                  <Copy size={16} />
                  Copy Link
                </button>
              )}

              {props.session.status !== 'completed' && (
                <button
                  onClick={downloadQrSvg}
                  class="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition"
                >
                  <QrCode size={16} />
                  QR Code
                </button>
              )}
            </div>
          </div>

          <h3 class="min-w-0 text-xl font-semibold text-slate-900 break-words">
            {props.session.title}
          </h3>

          {/* Metadata */}
            <div class="flex flex-wrap gap-2">
              <div class="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-50 text-slate-600 text-sm">
                <MapPin size={16} class="text-rose-400" />
                {props.session.location}
              </div>

              <div class="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-50 text-slate-600 text-sm">
                <Calendar size={16} class="text-blue-500" />
                {props.session.date}
              </div>

              <div class="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-50 text-slate-600 text-sm">
                <Clock size={16} class="text-amber-500" />
                {props.session.time}
              </div>

              <div class="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-50 text-slate-600 text-sm">
                <HelpCircle size={16} class="text-violet-500" />
                {props.session.questionsCount} questions
              </div>
            </div>
        </div>
      </div>
    )
  },
})
