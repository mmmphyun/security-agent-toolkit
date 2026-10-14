export default function EventList(props) {
  return (
    <section className="panel">
      <h2>최근 요청 기록</h2>
      <p className="muted">일반 서비스가 보낸 최근 50건입니다.</p>
      {props.events.length === 0 && <p>아직 수집된 요청이 없습니다. 일반 서비스에 접속한 뒤 목록 새로고침을 누르세요.</p>}
      <div className="table-scroll">
        <table>
          <thead><tr><th>시각</th><th>메서드</th><th>경로</th><th>상태 코드</th><th>분류</th></tr></thead>
          <tbody>
            {props.events.map(function (event) {
              return (
                <tr key={event.id}>
                  <td>{event.occurred_at}</td><td>{event.method}</td><td>{event.path}</td>
                  <td>{event.status_code}</td><td>{event.event_type}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
