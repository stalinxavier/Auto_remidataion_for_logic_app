import FailedMessagesTable from '../table/FailedMessagesTable'

export default function FailedMessagesPage() {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold text-gray-900">Failed Messages</h2>
        <p className="text-sm text-gray-500 mt-0.5">Messages that failed during integration processing</p>
      </div>
      <FailedMessagesTable />
    </div>
  )
}
